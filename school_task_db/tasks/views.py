import json

from django.shortcuts import redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import Http404, JsonResponse
from django.views.decorators.http import require_POST

from core_logic.entities.task import TaskListFilters
from core_logic.use_cases.bulk_change_task_groups import (
    BulkAddTasksToGroupRequest,
    BulkCreateGroupFromTasksRequest,
    BulkRemoveTasksFromGroupsRequest,
)
from core_logic.use_cases.delete_task import DeleteTaskRequest
from core_logic.use_cases.create_work_from_tasks import CreateWorkFromTasksRequest
from core_logic.use_cases.get_task_reference_options import (
    CodifierElementsResult,
    SubtopicOptionsResult,
)
from infrastructure.container import container
from .models import Task, Source
from .forms import TaskForm, SourceForm


class TaskListView(ListView):
    template_name = 'tasks/list.html'
    context_object_name = 'tasks'
    paginate_by = 20

    def _get_list_data(self):
        if not hasattr(self, '_task_list_data'):
            self._task_list_data = container.get_task_list_use_case().execute(
                TaskListFilters(
                    search=self.request.GET.get('search', ''),
                    topic_id=self.request.GET.get('topic', ''),
                    subtopic_id=self.request.GET.get('subtopic', ''),
                    task_type=self.request.GET.get('task_type', ''),
                    difficulty=self.request.GET.get('difficulty', ''),
                    group_filter=self.request.GET.get('group_filter', ''),
                    analog_group_id=self.request.GET.get('analog_group', ''),
                    math_filter=self.request.GET.get('math_filter', 'all'),
                    source_id=self.request.GET.get('source', ''),
                    grade=self.request.GET.get('grade', ''),
                    verified=self.request.GET.get('verified', ''),
                ),
                include_cache_stats=self.request.user.is_staff,
            )
        return self._task_list_data

    def get_queryset(self):
        return self._get_list_data().tasks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        list_data = self._get_list_data()
        context['topics'] = list_data.topics
        context['analog_groups'] = list_data.analog_groups
        context['sources'] = list_data.sources
        context['current_source'] = self.request.GET.get('source', '')
        context['current_grade'] = self.request.GET.get('grade', '')
        context['current_verified'] = self.request.GET.get('verified', '')
        context['grade_choices'] = list_data.grade_choices
        context['subtopics'] = list_data.subtopics
        context['task_types'] = list_data.task_types
        context['difficulties'] = list_data.difficulties

        # Текущие фильтры
        context['current_filter'] = self.request.GET.get('math_filter', 'all')
        context['search_query'] = self.request.GET.get('search', '')
        context['current_topic'] = self.request.GET.get('topic', '')
        context['current_subtopic'] = self.request.GET.get('subtopic', '')
        context['current_task_type'] = self.request.GET.get('task_type', '')
        context['current_difficulty'] = self.request.GET.get('difficulty', '')
        context['current_group_filter'] = self.request.GET.get('group_filter', '')
        context['current_analog_group'] = self.request.GET.get('analog_group', '')

        # Статистика
        context['total_tasks'] = list_data.total_tasks
        context['ungrouped_count'] = list_data.ungrouped_count

        if list_data.cache_stats is not None:
            context['cache_stats'] = list_data.cache_stats

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
        context['task'] = detail_data.task
        context['task_groups'] = detail_data.task_groups
        return context


class TaskCreateView(CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = container.task_form_adapter.build_image_formset(
                self.request.POST,
                self.request.FILES,
            )
        else:
            context['image_formset'] = (
                container.task_form_adapter.build_image_formset()
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']

        if image_formset.is_valid():
            result = container.task_form_adapter.save_created_task_with_images(
                form,
                image_formset,
            )
            self.object = result.task

            messages.success(self.request, 'Задание успешно создано!')
            if result.created_images > 0:
                messages.info(
                    self.request,
                    f'Добавлено изображений: {result.created_images}',
                )

            return redirect(self.object.get_absolute_url())
        else:
            messages.error(self.request, 'Ошибка при создании задания.')
            return self.form_invalid(form)


class TaskUpdateView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['image_formset'] = container.task_form_adapter.build_image_formset(
                self.request.POST,
                self.request.FILES,
                instance=self.object,
            )
        else:
            context['image_formset'] = container.task_form_adapter.build_image_formset(
                instance=self.object,
            )
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']

        if image_formset.is_valid():
            result = container.task_form_adapter.save_updated_task_with_images(
                form,
                image_formset,
            )
            self.object = result.task

            messages.success(self.request, 'Задание успешно обновлено!')
            if result.created_images > 0:
                messages.info(
                    self.request,
                    f'Добавлено изображений: {result.created_images}',
                )
            if result.deleted_images > 0:
                messages.info(
                    self.request,
                    f'Удалено изображений: {result.deleted_images}',
                )

            return redirect(self.object.get_absolute_url())
        else:
            messages.error(self.request, 'Ошибка при обновлении задания.')
            return self.form_invalid(form)


class TaskDeleteView(DeleteView):
    model = Task
    template_name = 'tasks/confirm_delete.html'
    context_object_name = 'task'
    success_url = reverse_lazy('tasks:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse('tasks:detail', kwargs={'pk': self.object.pk})
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        result = container.delete_task_use_case().execute(
            DeleteTaskRequest(task_id=str(self.object.pk)),
        )
        if result.success:
            messages.success(request, result.message)
        return redirect(self.get_success_url())


# === AJAX endpoints ===

def load_subtopics(request):
    """AJAX для загрузки подтем при выборе темы"""
    result = container.get_subtopic_options_use_case().execute(
        topic_id=request.GET.get('topic_id', ''),
    )
    return JsonResponse(_subtopic_options_payload(result))


def load_codifier_elements(request):
    """AJAX для загрузки элементов кодификатора"""
    result = container.get_codifier_elements_use_case().execute(
        subject=request.GET.get('subject', ''),
        category=request.GET.get('category', ''),
    )
    return JsonResponse(_codifier_elements_payload(result))


def _subtopic_options_payload(result: SubtopicOptionsResult):
    return {
        'subtopics': [
            {'id': option.id, 'name': option.name}
            for option in result.subtopics
        ],
    }


def _codifier_elements_payload(result: CodifierElementsResult):
    return {
        'elements': [
            {'code': element.code, 'name': element.name}
            for element in result.elements
        ],
    }


# === Bulk actions ===

@require_POST
def bulk_create_group(request):
    """Создать новую группу аналогов из выбранных заданий"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.bulk_create_group_from_tasks_use_case().execute(
        BulkCreateGroupFromTasksRequest(
            task_ids=body.get('task_ids', []),
            group_name=body.get('group_name', ''),
        )
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse({
        'success': True,
        'group_id': result.group_id,
        'group_name': result.group_name,
        'added': result.added_count,
        'message': result.message,
    })


@require_POST
def bulk_add_to_group(request):
    """Добавить выбранные задания в существующую группу"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.bulk_add_tasks_to_group_use_case().execute(
        BulkAddTasksToGroupRequest(
            task_ids=body.get('task_ids', []),
            group_id=body.get('group_id', ''),
        )
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse({
        'success': True,
        'added': result.added_count,
        'skipped': result.skipped_count,
        'message': result.message,
    })


@require_POST
def bulk_remove_from_groups(request):
    """Удалить выбранные задания из всех групп"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.bulk_remove_tasks_from_groups_use_case().execute(
        BulkRemoveTasksFromGroupsRequest(task_ids=body.get('task_ids', [])),
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse({
        'success': True,
        'removed': result.removed_count,
        'message': result.message,
    })


@require_POST
def bulk_create_work(request):
    """Создать работу с вариантом из выбранных заданий"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.create_work_from_tasks_use_case().execute(
        CreateWorkFromTasksRequest(
            task_ids=body.get('task_ids', []),
            work_name=body.get('work_name', ''),
            work_type=body.get('work_type', 'test'),
        )
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse({
        'success': True,
        'work_id': result.work_id,
        'variant_id': result.variant_id,
        'tasks_count': result.tasks_count,
        'redirect_url': f'/works/{result.work_id}/',
        'message': result.message,
    })


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


class SourceListView(ListView):
    template_name = 'tasks/source_list.html'
    context_object_name = 'sources'
    paginate_by = 20

    def get_queryset(self):
        return container.get_source_list_use_case().execute().sources


class SourceCreateView(CreateView):
    model = Source
    form_class = SourceForm
    template_name = 'tasks/source_form.html'

    def get_success_url(self):
        # Если открыто в popup — закрываем
        if self.request.GET.get('popup'):
            return reverse('tasks:source-created-popup', kwargs={'pk': self.object.pk})
        return reverse('tasks:source-list')

    def form_valid(self, form):
        self.object = container.task_form_adapter.save_source_form(form)
        messages.success(self.request, f'Источник «{self.object}» создан!')
        return redirect(self.get_success_url())
