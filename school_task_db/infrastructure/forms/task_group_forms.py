"""Infrastructure helpers for Django task group forms."""

from core_logic.entities.task import TaskGroupListFilters
from core_logic.use_cases.save_analog_group import SaveAnalogGroupRequest


class TaskGroupFormAdapter:
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
