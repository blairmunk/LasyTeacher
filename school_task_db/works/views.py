from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.views.decorators.http import require_http_methods

from .models import Work, Variant
from .forms import WorkForm, VariantGenerationForm


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


class WorkCreateView(CreateView):
    model = Work
    form_class = WorkForm
    template_name = 'works/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        if self.request.POST:
            context['formset'] = (
                container.work_form_adapter.build_analog_group_formset(
                    data=self.request.POST,
                )
            )
        else:
            context['formset'] = (
                container.work_form_adapter.build_analog_group_formset()
            )
        form_data = container.get_work_form_data_use_case().execute()
        context['analog_group_options'] = form_data.analog_group_options
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            response = super().form_valid(form)
            from infrastructure.container import container

            container.work_form_adapter.save_analog_group_formset(
                formset=formset,
                work=self.object,
            )
            messages.success(self.request, 'Работа успешно создана!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))


class WorkUpdateView(UpdateView):
    model = Work
    form_class = WorkForm
    template_name = 'works/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from infrastructure.container import container

        if self.request.POST:
            context['formset'] = (
                container.work_form_adapter.build_analog_group_formset(
                    data=self.request.POST,
                    instance=self.object,
                )
            )
        else:
            context['formset'] = (
                container.work_form_adapter.build_analog_group_formset(
                    instance=self.object,
                )
            )
        form_data = container.get_work_form_data_use_case().execute()
        context['analog_group_options'] = form_data.analog_group_options
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            response = super().form_valid(form)
            from infrastructure.container import container

            container.work_form_adapter.save_analog_group_formset(
                formset=formset,
                work=self.object,
            )
            messages.success(self.request, 'Работа успешно обновлена!')
            return response
        else:
            return self.render_to_response(self.get_context_data(form=form))


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
        'work': form_data.work, 'form': form,
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


class VariantListView(ListView):
    template_name = 'works/variant_list.html'
    context_object_name = 'variants'
    paginate_by = 20

    def get_queryset(self):
        from infrastructure.container import container

        return container.get_variant_list_use_case().execute().variants


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


class OrphanVariantListView(ListView):
    """Варианты без привязки к работе (сироты)"""

    template_name = 'works/orphan_variants.html'
    context_object_name = 'variants'
    paginate_by = 20

    def _get_orphan_list_data(self):
        if not hasattr(self, '_orphan_list_data'):
            from infrastructure.container import container

            self._orphan_list_data = (
                container.get_orphan_variant_list_use_case().execute()
            )
        return self._orphan_list_data

    def get_queryset(self):
        return self._get_orphan_list_data().variants

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_orphans'] = self._get_orphan_list_data().total_orphans
        return context


class VariantDeleteView(DeleteView):
    model = Variant
    template_name = 'works/variant_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        variant = self.object
        from infrastructure.container import container

        delete_info = container.get_variant_delete_info_use_case().execute(
            str(variant.pk),
        )
        context['variant'] = variant
        context['delete_info'] = delete_info
        context['task_count'] = delete_info.task_count
        context['has_grades'] = delete_info.has_participations
        context['grade_count'] = delete_info.participation_count

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        action = request.POST.get('action', 'delete')
        from core_logic.use_cases.delete_variant import DeleteVariantRequest
        from infrastructure.container import container

        result = container.delete_variant_use_case().execute(
            DeleteVariantRequest(
                variant_id=str(self.object.pk),
                action=action,
            )
        )

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
