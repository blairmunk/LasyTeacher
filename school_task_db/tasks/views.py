import json

from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib import messages
from django.urls import reverse
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST

from core_logic.use_cases.delete_task import DeleteTaskRequest
from infrastructure.container import container
from infrastructure.forms.task_django_forms import SourceForm


class TaskListView(TemplateView):
    template_name = 'tasks/list.html'
    paginate_by = 20

    def _get_list_data(self):
        if not hasattr(self, '_task_list_data'):
            self._task_list_data = container.get_task_list_use_case().execute(
                container.task_form_adapter.task_list_filters_from_query(
                    self.request.GET,
                ),
                include_cache_stats=self.request.user.is_staff,
            )
        return self._task_list_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        list_data = self._get_list_data()
        context.update(
            container.task_form_adapter.task_list_context(
                list_data,
                self.request.GET,
                self.paginate_by,
            )
        )
        return context


class TaskDetailView(TemplateView):
    template_name = 'tasks/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail_data = container.get_task_detail_use_case().execute(
            task_id=str(self.kwargs['pk']),
        )
        if detail_data.task is None:
            raise Http404('Задание не найдено')
        context.update(container.task_form_adapter.task_detail_context(detail_data))
        return context


class TaskCreateView(TemplateView):
    template_name = 'tasks/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            container.task_form_adapter.task_create_context(
                kwargs.get('form') or container.task_form_adapter.build_task_form(),
                kwargs.get('image_formset')
                or container.task_form_adapter.build_image_formset(),
            )
        )
        return context

    def post(self, request, *args, **kwargs):
        form = container.task_form_adapter.build_task_form(request.POST)
        image_formset = container.task_form_adapter.build_image_formset(
            request.POST,
            request.FILES,
        )

        if not form.is_valid() or not image_formset.is_valid():
            messages.error(request, 'Ошибка при создании задания.')
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    image_formset=image_formset,
                ),
            )

        task_result = container.create_task_use_case().execute(
            container.task_form_adapter.task_params_from_form(form),
        )
        image_result = container.save_task_images_use_case().execute(
            task_id=task_result.task_id,
            images=container.task_form_adapter.task_image_params_from_formset(
                image_formset,
            ),
        )

        messages.success(request, 'Задание успешно создано!')
        if image_result.created_images > 0:
            messages.info(
                request,
                f'Добавлено изображений: {image_result.created_images}',
            )

        return redirect(reverse('tasks:detail', kwargs={'pk': task_result.task_id}))


class TaskUpdateView(TemplateView):
    template_name = 'tasks/form.html'

    def _get_task(self):
        detail_data = container.get_task_detail_use_case().execute(
            task_id=str(self.kwargs['pk']),
        )
        if detail_data.task is None:
            raise Http404('Задание не найдено')
        return detail_data.task

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = kwargs.get('object') or self._get_task()
        form = (
            kwargs.get('form')
            or container.task_form_adapter.build_task_form(task_id=str(task.pk))
        )
        image_formset = (
            kwargs.get('image_formset')
            or container.task_form_adapter.build_image_formset_for_task(
                task_id=str(task.pk),
            )
        )
        context.update(
            container.task_form_adapter.task_update_context(
                task,
                form,
                image_formset,
            )
        )
        return context

    def post(self, request, *args, **kwargs):
        task = self._get_task()
        form = container.task_form_adapter.build_task_form(
            request.POST,
            task_id=str(task.pk),
        )
        image_formset = container.task_form_adapter.build_image_formset_for_task(
            data=request.POST,
            files=request.FILES,
            task_id=str(task.pk),
        )

        if not form.is_valid() or not image_formset.is_valid():
            messages.error(request, 'Ошибка при обновлении задания.')
            return self.render_to_response(
                self.get_context_data(
                    form=form,
                    image_formset=image_formset,
                    object=task,
                ),
            )

        task_result = container.update_task_use_case().execute(
            container.task_form_adapter.task_params_from_form(
                form,
                task_id=str(task.pk),
            ),
        )
        if task_result.status == 'not_found':
            raise Http404('Задание не найдено')

        image_result = container.save_task_images_use_case().execute(
            task_id=task_result.task_id,
            images=container.task_form_adapter.task_image_params_from_formset(
                image_formset,
            ),
        )

        messages.success(request, 'Задание успешно обновлено!')
        if image_result.created_images > 0:
            messages.info(
                request,
                f'Добавлено изображений: {image_result.created_images}',
            )
        if image_result.deleted_images > 0:
            messages.info(
                request,
                f'Удалено изображений: {image_result.deleted_images}',
            )

        return redirect(reverse('tasks:detail', kwargs={'pk': task_result.task_id}))


class TaskDeleteView(TemplateView):
    template_name = 'tasks/confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail_data = container.get_task_detail_use_case().execute(
            task_id=str(self.kwargs['pk']),
        )
        if detail_data.task is None:
            raise Http404('Задание не найдено')
        context.update(
            container.task_form_adapter.task_delete_context(
                detail_data,
                cancel_url=reverse(
                    'tasks:detail',
                    kwargs={'pk': self.kwargs['pk']},
                ),
            )
        )
        return context

    def post(self, request, *args, **kwargs):
        result = container.delete_task_use_case().execute(
            DeleteTaskRequest(task_id=str(self.kwargs['pk'])),
        )
        if result.success:
            messages.success(request, result.message)
        return redirect(reverse('tasks:list'))


# === AJAX endpoints ===

def load_subtopics(request):
    """AJAX для загрузки подтем при выборе темы"""
    result = container.get_subtopic_options_use_case().execute(
        topic_id=container.task_form_adapter.subtopic_options_topic_id_from_query(
            request.GET,
        ),
    )
    return JsonResponse(container.task_form_adapter.subtopic_options_payload(result))


def load_codifier_elements(request):
    """AJAX для загрузки элементов кодификатора"""
    params = container.task_form_adapter.codifier_elements_params_from_query(
        request.GET,
    )
    result = container.get_codifier_elements_use_case().execute(
        subject=params['subject'],
        category=params['category'],
    )
    return JsonResponse(container.task_form_adapter.codifier_elements_payload(result))


# === Bulk actions ===

@require_POST
def bulk_create_group(request):
    """Создать новую группу аналогов из выбранных заданий"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.bulk_create_group_from_tasks_use_case().execute(
        container.task_form_adapter.bulk_create_group_request_from_body(body),
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse(
        container.task_form_adapter.bulk_create_group_response_payload(result),
    )


@require_POST
def bulk_add_to_group(request):
    """Добавить выбранные задания в существующую группу"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.bulk_add_tasks_to_group_use_case().execute(
        container.task_form_adapter.bulk_add_to_group_request_from_body(body),
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse(
        container.task_form_adapter.bulk_add_to_group_response_payload(result),
    )


@require_POST
def bulk_remove_from_groups(request):
    """Удалить выбранные задания из всех групп"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.bulk_remove_tasks_from_groups_use_case().execute(
        container.task_form_adapter.bulk_remove_from_groups_request_from_body(body),
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse(
        container.task_form_adapter.bulk_remove_from_groups_response_payload(
            result,
        ),
    )


@require_POST
def bulk_create_work(request):
    """Создать работу с вариантом из выбранных заданий"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.create_work_from_tasks_use_case().execute(
        container.task_form_adapter.create_work_from_tasks_request_from_body(body),
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse(
        container.task_form_adapter.create_work_from_tasks_response_payload(
            result,
        ),
    )


def refresh_math_cache(request):
    """Принудительное обновление кэша формул"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Доступ запрещен'}, status=403)

    try:
        result = container.refresh_task_math_cache_use_case().execute()
        return JsonResponse({
            'success': True,
            'message': result.message,
            'stats': {
                'with_math': result.with_math_count,
                'with_errors': result.with_errors_count,
                'with_warnings': result.with_warnings_count,
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


class SourceListView(TemplateView):
    template_name = 'tasks/source_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        list_data = container.get_source_list_use_case().execute()
        context.update(container.task_form_adapter.source_list_context(list_data))
        return context


class SourceCreateView(TemplateView):
    template_name = 'tasks/source_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            container.task_form_adapter.source_create_context(
                kwargs.get('form') or SourceForm(),
            )
        )
        return context

    def post(self, request, *args, **kwargs):
        form = SourceForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        result = container.create_source_use_case().execute(
            container.task_form_adapter.source_params_from_form(form),
        )
        messages.success(
            self.request,
            f'Источник «{result.display_name}» создан!',
        )
        return redirect(reverse('tasks:source-list'))
