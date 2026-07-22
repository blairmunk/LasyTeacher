import json

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.views.decorators.http import require_POST
from django.http import Http404, JsonResponse

from core_logic.use_cases.change_task_group_membership import (
    RemoveTaskFromGroupRequest,
)
from core_logic.use_cases.create_work_from_groups import (
    PrepareCreateWorkFromGroupsSubmissionRequest,
)
from core_logic.use_cases.prepare_task_group_membership_submission import (
    PrepareAddTasksToGroupSubmissionRequest,
    PrepareUpdateTaskGroupRolesSubmissionRequest,
)
from infrastructure.container import container
from infrastructure.forms.task_group_django_forms import AnalogGroupForm
from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_SPECIFIC_CHOICES,
)


def _post_lists(post_data):
    return {
        key: post_data.getlist(key)
        for key in post_data
    }


class AnalogGroupListView(TemplateView):
    template_name = 'task_groups/list.html'
    paginate_by = 20

    def _get_list_data(self):
        if not hasattr(self, '_task_group_list_data'):
            self._task_group_list_data = (
                container.get_task_group_list_use_case().execute(
                    container.task_group_form_adapter
                    .task_group_list_filters_from_query(
                        self.request.GET,
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
        context.update(
            container.task_group_form_adapter
            .task_group_list_filter_context_from_query(
                self.request.GET,
            )
        )

        # Статистика
        context['total_groups'] = list_data.total_groups
        context['empty_groups'] = list_data.empty_groups
        context['total_tasks_in_groups'] = list_data.total_tasks_in_groups
        context['bank_role_filter_options'] = tuple(
            (value, label)
            for value, label in (
                (TASK_BANK_ROLE_ANY, 'Любая роль'),
                *TASK_BANK_ROLE_SPECIFIC_CHOICES,
            )
        )

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
        context['bank_role_options'] = TASK_BANK_ROLE_SPECIFIC_CHOICES
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
            container.task_group_form_adapter.analog_group_params_from_form(form),
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
            initial=container.task_group_form_adapter.analog_group_form_initial(group),
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
            container.task_group_form_adapter.analog_group_params_from_form(
                form,
                group_id=str(group.pk),
            )
        )
        if result.status == 'not_found':
            raise Http404('Группа аналогов не найдена')

        messages.success(request, 'Группа аналогов успешно обновлена!')
        return redirect('task_groups:detail', pk=result.group_id)


def add_tasks_to_group(request, group_id):
    """Добавление заданий в группу аналогов"""
    if request.method == 'POST':
        add_request = container.prepare_add_tasks_to_group_submission_use_case().execute(
            PrepareAddTasksToGroupSubmissionRequest(
                group_id=str(group_id),
                data=_post_lists(request.POST),
            )
        )

        result = container.add_tasks_to_group_use_case().execute(
            add_request,
        )
        if result.status == 'not_found':
            raise Http404("Группа не найдена")
        if result.status == 'invalid':
            messages.error(request, '; '.join(result.errors))
            return redirect('task_groups:add-tasks', group_id=group_id)
        if result.created_count:
            messages.success(
                request,
                f'Добавлено {result.created_count} заданий '
                f'в группу "{result.group_name}"',
            )
        return redirect('task_groups:detail', pk=group_id)

    data = container.get_add_tasks_to_group_use_case().execute(
        container.task_group_form_adapter.add_tasks_to_group_form_request_from_query(
            request.GET,
            group_id=str(group_id),
        )
    )
    if data.status == 'not_found':
        raise Http404("Группа не найдена")

    context = {
        'group': data.group,
        'available_tasks': data.available_tasks,
        'search': data.search,
        'bank_role_options': TASK_BANK_ROLE_SPECIFIC_CHOICES,
        'selected_bank_role': TASK_BANK_ROLE_CONTROL,
    }
    return render(request, 'task_groups/add_tasks.html', context)


def remove_task_from_group(request, group_id, task_id):
    """Удаление задания из группы аналогов"""
    if request.method == 'POST':
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


@require_POST
def update_task_group_roles(request, group_id):
    update_request = (
        container.prepare_update_task_group_roles_submission_use_case().execute(
            PrepareUpdateTaskGroupRolesSubmissionRequest(
                group_id=str(group_id),
                data=_post_lists(request.POST),
            )
        )
    )
    result = container.update_task_group_roles_use_case().execute(update_request)
    if result.status == 'not_found':
        raise Http404("Группа не найдена")
    if result.status == 'invalid':
        messages.error(request, '; '.join(result.errors))
        return redirect('task_groups:detail', pk=group_id)

    messages.success(
        request,
        f'Обновлено ролей: {result.updated_count}',
    )
    return redirect('task_groups:detail', pk=group_id)


# === Bulk actions ===

@require_POST
def bulk_create_work_from_groups(request):
    """Создать работу из выбранных групп аналогов"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    create_request = (
        container.prepare_create_work_from_groups_submission_use_case().execute(
            PrepareCreateWorkFromGroupsSubmissionRequest(body=body),
        )
    )
    result = container.create_work_from_groups_use_case().execute(create_request)

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    payload = (
        container.task_group_form_adapter
        .create_work_from_groups_response_payload(result)
    )
    return JsonResponse(payload)


@require_POST
def bulk_delete_groups(request):
    """Удалить выбранные группы"""
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Невалидный JSON'}, status=400)

    result = container.delete_task_groups_use_case().execute(
        container.task_group_form_adapter.delete_task_groups_request_from_body(body),
    )

    if not result.success:
        return JsonResponse({'error': result.message}, status=400)

    return JsonResponse(
        container.task_group_form_adapter.delete_task_groups_response_payload(
            result,
        ),
    )
