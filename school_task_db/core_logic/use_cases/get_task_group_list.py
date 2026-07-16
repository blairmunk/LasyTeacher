"""Build analog group list screen data."""

from core_logic.entities.task import TaskGroupListData, TaskGroupListFilters
from core_logic.interfaces.task_repo import ITaskRepository


class GetTaskGroupListUseCase:
    def __init__(self, task_repo: ITaskRepository):
        self.task_repo = task_repo

    def execute(self, filters: TaskGroupListFilters) -> TaskGroupListData:
        return TaskGroupListData(
            analog_groups=self.task_repo.get_list_task_groups(filters),
            topics=self.task_repo.get_list_topics(),
            subtopics=self.task_repo.get_subtopics_for_topic(filters.topic_id),
            difficulties=[
                (1, 'Базовый'),
                (2, 'Повышенный'),
                (3, 'Высокий'),
            ],
            total_groups=self.task_repo.count_analog_groups(),
            empty_groups=self.task_repo.count_empty_analog_groups(),
            total_tasks_in_groups=self.task_repo.count_task_group_memberships(),
        )
