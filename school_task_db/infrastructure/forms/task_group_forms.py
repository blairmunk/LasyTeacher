"""Infrastructure helpers for Django task group forms."""

from core_logic.entities.task import TaskGroupListFilters
from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsRequest
from core_logic.use_cases.get_add_tasks_to_group import AddTasksToGroupFormRequest
from core_logic.use_cases.save_analog_group import SaveAnalogGroupRequest


class TaskGroupFormAdapter:
    def add_tasks_to_group_form_request_from_query(self, query, group_id):
        return AddTasksToGroupFormRequest(
            group_id=group_id,
            search=query.get('search', ''),
        )

    def delete_task_groups_request_from_body(self, body):
        return DeleteTaskGroupsRequest(group_ids=body.get('group_ids', []))

    def create_work_from_groups_response_payload(self, result):
        payload = {
            'success': True,
            'work_id': result.work_id,
            'redirect_url': f'/works/{result.work_id}/',
            'message': result.message,
        }
        if result.variants_generated:
            payload['variants_generated'] = result.variants_generated
        if result.warning:
            payload['warning'] = result.warning
        return payload

    def delete_task_groups_response_payload(self, result):
        return {
            'success': True,
            'deleted': result.deleted_count,
            'message': result.message,
        }

    def task_group_list_filters_from_query(self, query):
        return TaskGroupListFilters(
            search=query.get('search', ''),
            topic_id=query.get('topic', ''),
            subtopic_id=query.get('subtopic', ''),
            difficulty=query.get('difficulty', ''),
            group_filter=query.get('group_filter', ''),
            sort=query.get('sort', 'name'),
            min_tasks=query.get('min_tasks', ''),
            max_tasks=query.get('max_tasks', ''),
        )

    def task_group_list_filter_context_from_query(self, query):
        return {
            'search_query': query.get('search', ''),
            'current_topic': query.get('topic', ''),
            'current_subtopic': query.get('subtopic', ''),
            'current_difficulty': query.get('difficulty', ''),
            'current_group_filter': query.get('group_filter', ''),
            'current_sort': query.get('sort', 'name'),
            'min_tasks': query.get('min_tasks', ''),
            'max_tasks': query.get('max_tasks', ''),
        }

    def analog_group_params_from_form(self, form, group_id=''):
        return SaveAnalogGroupRequest(
            group_id=group_id,
            name=form.cleaned_data['name'],
            description=form.cleaned_data.get('description', ''),
        )

    def analog_group_form_initial(self, group):
        return {
            'name': group.name,
            'description': group.description,
        }
