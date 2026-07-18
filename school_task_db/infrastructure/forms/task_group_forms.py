"""Infrastructure helpers for Django task group forms."""

from core_logic.entities.task import TaskGroupListFilters
from core_logic.use_cases.create_work_from_groups import (
    CreateWorkFromGroupsRequest,
    GroupSpecRequest,
)
from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsRequest
from core_logic.use_cases.save_analog_group import SaveAnalogGroupRequest


class TaskGroupFormAdapter:
    def create_work_from_groups_request_from_body(self, body):
        groups_data = body.get('groups', [])
        return CreateWorkFromGroupsRequest(
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

    def delete_task_groups_request_from_body(self, body):
        return DeleteTaskGroupsRequest(group_ids=body.get('group_ids', []))

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
