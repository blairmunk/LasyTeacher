from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
from django.http import Http404, JsonResponse

from core_logic.entities.task import TaskGroupListFilters
from core_logic.use_cases.get_add_tasks_to_group import AddTasksToGroupFormRequest
from core_logic.use_cases.save_analog_group import SaveAnalogGroupRequest
from infrastructure.container import container
from .forms import AnalogGroupForm


class AnalogGroupListView(TemplateView):
    template_name = 'task_groups/list.html'
    paginate_by = 20

    def _get_list_data(self):
        if not hasattr(self, '_task_group_list_data'):
            self._task_group_list_data = (
                container.get_task_group_list_use_case().execute(
                    TaskGroupListFilters(
                        search=self.request.GET.get('search', ''),
                        topic_id=self.request.GET.get('topic', ''),
                        subtopic_id=self.request.GET.get('subtopic', ''),
                        difficulty=self.request.GET.get('difficulty', ''),
                        group_filter=self.request.GET.get('group_filter', ''),
                        sort=self.request.GET.get('sort', 'name'),
                        min_tasks=self.request.GET.get('min_tasks', ''),
                        max_tasks=self.request.GET.get('max_tasks', ''),
                    )
                )
            )
        return self._task_group_list_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        list_data = self._get_list_data()
        paginator = Paginator(list_data.analog_groups, self.paginate_by)
        page_obj = paginator.get_page(self.request.GET.get('page'))

        context['analog_groups'] = page_obj.object_list
        context['page_obj'] = page_obj
        context['is_paginated'] = page_obj.has_other_pages()
        context['topics'] = list_data.topics
        context['subtopics'] = list_data.subtopics
        context['difficulties'] = list_data.difficulties

        # Текущие фильтры
        context['search_query'] = self.request.GET.get('search', '')
        context['current_topic'] = self.request.GET.get('topic', '')
        context['current_subtopic'] = self.request.GET.get('subtopic', '')
        context['current_difficulty'] = self.request.GET.get('difficulty', '')
        context['current_group_filter'] = self.request.GET.get('group_filter', '')
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['min_tasks'] = self.request.GET.get('min_tasks', '')
        context['max_tasks'] = self.request.GET.get('max_tasks', '')

        # Статистика
        context['total_groups'] = list_data.total_groups
        context['empty_groups'] = list_data.empty_groups
        context['total_tasks_in_groups'] = list_data.total_tasks_in_groups

        return context


class AnalogGroupDetailView(TemplateView):
    template_name = 'task_groups/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        detail_data = container.get_task_group_detail_use_case().execute(
            str(self.kwargs['pk']),
        )
        if detail_data.group is None:
            raise Http404('Группа аналогов не найдена')
        context['analoggroup'] = detail_data.group
        context['tasks'] = detail_data.tasks
        return context


class AnalogGroupCreateView(TemplateView):
    template_name = 'task_groups/form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = kwargs.get('form') or AnalogGroupForm()
        return context

    def post(self, request, *args, **kwargs):
        form = AnalogGroupForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form))

        result = container.create_analog_group_use_case().execute(
            SaveAnalogGroupRequest(
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
            )
        )
        messages.success(request, 'Группа аналогов успешно создана!')
        return redirect('task_groups:detail', pk=result.group_id)


class AnalogGroupUpdateView(TemplateView):
    template_name = 'task_groups/form.html'

    def _get_group_data(self):
        detail_data = container.get_task_group_detail_use_case().execute(
            str(self.kwargs['pk']),
        )
        if detail_data.group is None:
            raise Http404('Группа аналогов не найдена')
        return detail_data.group

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = kwargs.get('object') or self._get_group_data()
        context['object'] = group
        context['form'] = kwargs.get('form') or AnalogGroupForm(
            initial={
                'name': group.name,
                'description': group.description,
            }
        )
        return context

    def post(self, request, *args, **kwargs):
        group = self._get_group_data()
        form = AnalogGroupForm(request.POST)
        if not form.is_valid():
            return self.render_to_response(
                self.get_context_data(form=form, object=group),
            )

        result = container.update_analog_group_use_case().execute(
            SaveAnalogGroupRequest(
                group_id=str(group.pk),
                name=form.cleaned_data['name'],
                description=form.cleaned_data.get('description', ''),
            )
        )
        if result.status == 'not_found':
            raise Http404('Группа аналогов не найдена')

        messages.success(request, 'Группа аналогов успешно обновлена!')
        return redirect('task_groups:detail', pk=result.group_id)


def add_tasks_to_group(request, group_id):
    """Добавление заданий в группу аналогов"""
    if request.method == 'POST':
        from core_logic.use_cases.change_task_group_membership import (
            AddTasksToGroupRequest,
        )

        result = container.add_tasks_to_group_use_case().execute(
            AddTasksToGroupRequest(
                group_id=str(group_id),
                task_ids=request.POST.getlist('selected_tasks'),
            )
        )
        if result.status == 'not_found':
            raise Http404("Группа не найдена")
        if result.created_count:
            messages.success(
                request,
                f'Добавлено {result.created_count} заданий '
                f'в группу "{result.group_name}"',
            )
        return redirect('task_groups:detail', pk=group_id)

    data = container.get_add_tasks_to_group_use_case().execute(
        AddTasksToGroupFormRequest(
            group_id=str(group_id),
            search=request.GET.get('search', ''),
        )
    )
    if data.status == 'not_found':
        raise Http404("Группа не найдена")

    context = {
        'group': data.group,
        'available_tasks': data.available_tasks,
        'search': data.search,
    }
    return render(request, 'task_groups/add_tasks.html', context)


def remove_task_from_group(request, group_id, task_id):
    """Удаление задания из группы аналогов"""
    if request.method == 'POST':
        from core_logic.use_cases.change_task_group_membership import (
            RemoveTaskFromGroupRequest,
        )
        from infrastructure.container import container

        result = container.remove_task_from_group_use_case().execute(
            RemoveTaskFromGroupRequest(
                group_id=str(group_id),
                task_id=str(task_id),
            )
        )
        if result.status == 'not_found':
            raise Http404("Группа не найдена")
        messages.success(request, f'Задание удалено из группы "{result.group_name}"')

    return redirect('task_groups:detail', pk=group_id)


# === Bulk actions ===

@require_POST
def bulk_create_work_from_groups(request):
    """Создать работу из выбранных групп аналогов"""
    import json
    from core_logic.use_cases.create_work_from_groups import (
        CreateWorkFromGroupsRequest,
        GroupSpecRequest,
    )
    from infrastructure.container import container

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    groups_data = body.get('groups', [])
    result = container.create_work_from_groups_use_case().execute(
        CreateWorkFromGroupsRequest(
            groups=[
                GroupSpecRequest(
                    id=str(group_data.get('id', '')),
                    order=int(group_data.get('order', index)),
                    count=int(group_data.get('count', 1)),
                    weight=int(group_data.get('weight', 1)),
                )
                for index, group_data in enumerate(groups_data, 1)
            ],
            work_name=body.get('work_name', ''),
            work_type=body.get('work_type', 'test'),
            max_score=int(body.get('max_score', 0)),
            auto_generate=body.get('auto_generate', False),
            variant_count=int(body.get('variant_count', 2)),
        )
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    response = {
        'success': True,
        'work_id': result.work_id,
        'redirect_url': f'/works/{result.work_id}/',
        'message': result.message,
    }
    if result.variants_generated:
        response['variants_generated'] = result.variants_generated
    if result.warning:
        response['warning'] = result.warning

    return JsonResponse(response)



@require_POST
def bulk_delete_groups(request):
    """Удалить выбранные группы"""
    import json
    from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsRequest
    from infrastructure.container import container

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.delete_task_groups_use_case().execute(
        DeleteTaskGroupsRequest(group_ids=body.get('group_ids', [])),
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse({
        'success': True,
        'deleted': result.deleted_count,
        'message': result.message,
    })
