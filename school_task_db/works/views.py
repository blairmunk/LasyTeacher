from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.views.generic import TemplateView
from django.views.decorators.http import require_http_methods

from core_logic.interfaces.work_repo import CreateWorkParams
from .models import Work
from .forms import WorkForm, VariantGenerationForm


def _work_params_from_form(form, work_id=''):
    return CreateWorkParams(
        work_id=work_id,
        name=form.cleaned_data['name'],
        work_type=form.cleaned_data.get('work_type', 'test'),
        duration=form.cleaned_data.get('duration') or 45,
        max_score=form.cleaned_data.get('max_score') or 0,
    )


class WorkListView(TemplateView):
    template_name = 'works/list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        context['works'] = container.get_work_list_use_case().execute().works
        return context


class WorkDetailView(TemplateView):
    template_name = 'works/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        detail = container.get_work_detail_use_case().execute(str(self.kwargs['pk']))
        if detail.work is None:
            raise Http404('Работа не найдена')
        context['work'] = detail.work
        context['object'] = detail.work
        context['variants'] = detail.variants
        context['analog_groups'] = detail.analog_groups
        context['spec_preview'] = detail.spec_preview
        context['show_sync_button'] = detail.show_sync_button
        return context


class WorkCreateView(TemplateView):
    template_name = 'works/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        context['form'] = kwargs.get('form') or WorkForm()
        context['formset'] = (
            kwargs.get('formset')
            or container.work_form_adapter.build_analog_group_formset()
        )
        form_data = container.get_work_form_data_use_case().execute()
        context['analog_group_options'] = form_data.analog_group_options
        return context

    def post(self, request, *args, **kwargs):
        from infrastructure.container import container

        form = WorkForm(request.POST)
        formset = container.work_form_adapter.build_analog_group_formset(
            data=request.POST,
        )
        if not form.is_valid() or not formset.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, formset=formset),
            )

        result = container.create_work_use_case().execute(
            _work_params_from_form(form),
        )
        work = Work.objects.get(pk=result.work_id)
        container.work_form_adapter.save_analog_group_formset(
            formset=formset,
            work=work,
        )
        messages.success(request, 'Работа успешно создана!')
        return redirect('works:detail', pk=work.pk)


class WorkUpdateView(TemplateView):
    template_name = 'works/form.html'

    def _get_work(self):
        work = Work.objects.filter(pk=self.kwargs['pk']).first()
        if work is None:
            raise Http404('Работа не найдена')
        return work

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        work = kwargs.get('object') or self._get_work()
        context['object'] = work
        context['form'] = kwargs.get('form') or WorkForm(instance=work)
        context['formset'] = (
            kwargs.get('formset')
            or container.work_form_adapter.build_analog_group_formset(
                instance=work,
            )
        )
        form_data = container.get_work_form_data_use_case().execute()
        context['analog_group_options'] = form_data.analog_group_options
        return context

    def post(self, request, *args, **kwargs):
        from infrastructure.container import container

        work = self._get_work()
        form = WorkForm(request.POST, instance=work)
        formset = container.work_form_adapter.build_analog_group_formset(
            data=request.POST,
            instance=work,
        )
        if not form.is_valid() or not formset.is_valid():
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    formset=formset,
                    object=work,
                ),
            )

        result = container.update_work_use_case().execute(
            _work_params_from_form(form, work_id=str(work.pk)),
        )
        if result.status == 'not_found':
            raise Http404('Работа не найдена')

        container.work_form_adapter.save_analog_group_formset(
            formset=formset,
            work=work,
        )
        messages.success(request, 'Работа успешно обновлена!')
        return redirect('works:detail', pk=result.work_id)


def generate_variants(request, work_id):
    from infrastructure.container import container

    if request.method == 'POST':
        form = VariantGenerationForm(request.POST)
        if form.is_valid():
            count = form.cleaned_data['count']
            try:
                from core_logic.use_cases.generate_work_variants import (
                    GenerateWorkVariantsRequest,
                )
                result = container.generate_work_variants_use_case().execute(
                    GenerateWorkVariantsRequest(
                        work_id=str(work_id),
                        count=count,
                    )
                )
                if result.status == 'not_found':
                    raise Http404("Работа не найдена")
                messages.success(
                    request,
                    f'Успешно создано {result.created_count} вариантов!',
                )
                return redirect('works:detail', pk=work_id)
            except Http404:
                raise
            except Exception as e:
                messages.error(request, f'Ошибка при создании вариантов: {str(e)}')
    else:
        form = VariantGenerationForm()
    form_data = container.get_variant_generation_form_use_case().execute(
        str(work_id),
    )
    if form_data.status == 'not_found':
        raise Http404("Работа не найдена")
    return render(request, 'works/generate_variants.html', {
        'work': form_data.work,
        'work_groups': form_data.work_groups,
        'form': form,
    })


def sync_analog_groups(request, work_id):
    from infrastructure.container import container

    if request.method == 'POST':
        from core_logic.use_cases.sync_work_analog_groups import (
            SyncWorkAnalogGroupsRequest,
        )

        result = container.sync_work_analog_groups_use_case().execute(
            SyncWorkAnalogGroupsRequest(work_id=str(work_id)),
        )
        if result.status == 'not_found':
            raise Http404("Работа не найдена")
        if result.created_count > 0:
            messages.success(
                request,
                f'Создано {result.created_count} групп заданий из вариантов.',
            )
        else:
            messages.info(request, 'Группы заданий уже соответствуют вариантам.')
        return redirect('works:detail', pk=work_id)

    form_data = container.get_variant_generation_form_use_case().execute(
        str(work_id),
    )
    if form_data.status == 'not_found':
        raise Http404("Работа не найдена")
    return redirect('works:detail', pk=work_id)


class VariantListView(TemplateView):
    template_name = 'works/variant_list.html'
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        list_data = container.get_variant_list_use_case().execute()
        paginator = Paginator(list_data.variants, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        context['variants'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        return context


class VariantDetailView(TemplateView):
    template_name = 'works/variant_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        detail = container.get_variant_detail_use_case().execute(
            str(self.kwargs['pk']),
        )
        if detail.variant is None:
            raise Http404('Вариант не найден')
        context['variant'] = detail.variant
        context['object'] = detail.variant
        context['variant_tasks'] = detail.variant_tasks
        context['total_max_points'] = detail.total_max_points
        return context


class OrphanVariantListView(TemplateView):
    """Варианты без привязки к работе (сироты)"""

    template_name = 'works/orphan_variants.html'
    paginate_by = 20

    def _get_orphan_list_data(self):
        if not hasattr(self, '_orphan_list_data'):
            from infrastructure.container import container

            self._orphan_list_data = (
                container.get_orphan_variant_list_use_case().execute()
            )
        return self._orphan_list_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        list_data = self._get_orphan_list_data()
        paginator = Paginator(list_data.variants, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        context['variants'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['total_orphans'] = list_data.total_orphans
        return context


class VariantDeleteView(TemplateView):
    template_name = 'works/variant_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        delete_info = container.get_variant_delete_info_use_case().execute(
            str(self.kwargs['pk']),
        )
        if delete_info is None:
            raise Http404('Вариант не найден')

        context['delete_info'] = delete_info
        context['task_count'] = delete_info.task_count
        context['has_grades'] = delete_info.has_participations
        context['grade_count'] = delete_info.participation_count

        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action', 'delete')
        from core_logic.use_cases.delete_variant import DeleteVariantRequest
        from infrastructure.container import container

        result = container.delete_variant_use_case().execute(
            DeleteVariantRequest(
                variant_id=str(self.kwargs['pk']),
                action=action,
            )
        )

        if result.status == 'not_found':
            raise Http404('Вариант не найден')

        if result.status == 'blocked_has_participations':
            messages.error(
                request,
                'Невозможно удалить: за вариант есть оценки. Используйте «Отвязать».',
            )
            return self.get(request, *args, **kwargs)

        if result.status == 'detached':
            messages.success(
                request,
                f'Вариант #{result.variant_short_id} отвязан от работы (стал сиротой).',
            )
            return redirect('works:variant-list')

        if result.redirect_work_id:
            return redirect('works:detail', pk=result.redirect_work_id)
        return redirect('works:variant-list')


def bulk_delete_variants(request, work_id):
    """Удаление нескольких вариантов работы"""
    from django.http import JsonResponse

    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)

    variant_ids = request.POST.getlist('variant_ids')
    from core_logic.use_cases.bulk_delete_variants import (
        BulkDeleteVariantsRequest,
    )
    from infrastructure.container import container

    result = container.bulk_delete_variants_use_case().execute(
        BulkDeleteVariantsRequest(
            work_id=str(work_id),
            variant_ids=variant_ids,
        )
    )

    if result.status == 'empty_selection':
        return JsonResponse({'error': 'Не выбраны варианты'}, status=400)

    return JsonResponse({
        'success': True,
        'deleted': result.deleted_count,
        'remaining': result.remaining_count,
    })


@require_http_methods(["POST"])
def create_work_from_orphans(request):
    """Создать работу из выбранных вариантов-сирот"""
    variant_ids = request.POST.getlist('variant_ids')
    work_name = request.POST.get('work_name', '')

    from core_logic.use_cases.create_work_from_orphans import (
        CreateWorkFromOrphansRequest,
    )
    from infrastructure.container import container

    result = container.create_work_from_orphans_use_case().execute(
        CreateWorkFromOrphansRequest(
            variant_ids=variant_ids,
            work_name=work_name,
        )
    )

    if result.status == 'empty_selection':
        messages.warning(request, 'Не выбрано ни одного варианта.')
        return redirect('works:orphan-variants')

    if result.status == 'not_found':
        messages.error(request, 'Выбранные варианты не найдены или уже привязаны.')
        return redirect('works:orphan-variants')

    messages.success(
        request,
        f'Создана работа «{result.work_name}» с {result.variant_count} вариантами. '
        f'Теперь можно генерировать PDF!'
    )
    return redirect('works:detail', pk=result.work_id)
