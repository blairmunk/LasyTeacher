"""Build analog group list screen data."""

from core_logic.entities.task import TaskGroupListData, TaskGroupListFilters
from core_logic.interfaces.task_catalog_repo import ITaskCatalogRepository
from core_logic.interfaces.task_group_catalog_repo import (
    ITaskGroupCatalogRepository,
)


class GetTaskGroupListUseCase:
    def __init__(
        self,
        task_catalog_repo: ITaskCatalogRepository,
        task_group_repo: ITaskGroupCatalogRepository,
    ):
        self.task_catalog_repo = task_catalog_repo
        self.task_group_repo = task_group_repo

    def execute(self, filters: TaskGroupListFilters) -> TaskGroupListData:
        return TaskGroupListData(
            analog_groups=self.task_group_repo.get_list_task_groups(filters),
            topics=self.task_catalog_repo.get_list_topics(),
            subtopics=self.task_catalog_repo.get_subtopics_for_topic(
                filters.topic_id,
            ),
            difficulties=[
                (1, 'Базовый'),
                (2, 'Повышенный'),
                (3, 'Высокий'),
            ],
            total_groups=self.task_group_repo.count_analog_groups(),
            empty_groups=self.task_group_repo.count_empty_analog_groups(),
            total_tasks_in_groups=(
                self.task_group_repo.count_task_group_memberships()
            ),
        )
