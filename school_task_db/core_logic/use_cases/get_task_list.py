"""Build task list screen data."""

from core_logic.entities.task import TaskListData, TaskListFilters
from core_logic.interfaces.task_catalog_repo import ITaskCatalogRepository
from core_logic.interfaces.task_group_catalog_repo import (
    ITaskGroupCatalogRepository,
)
from core_logic.interfaces.task_math_status_cache import ITaskMathStatusCache
from core_logic.interfaces.task_read_repo import ITaskReadRepository


class GetTaskListUseCase:
    def __init__(
        self,
        task_repo: ITaskReadRepository,
        task_catalog_repo: ITaskCatalogRepository,
        task_group_repo: ITaskGroupCatalogRepository,
        math_status_cache: ITaskMathStatusCache,
    ):
        self.task_repo = task_repo
        self.task_catalog_repo = task_catalog_repo
        self.task_group_repo = task_group_repo
        self.math_status_cache = math_status_cache

    def execute(
        self,
        filters: TaskListFilters,
        include_cache_stats: bool = False,
    ) -> TaskListData:
        return TaskListData(
            tasks=self.task_repo.get_list_tasks(filters),
            topics=self.task_catalog_repo.get_list_topics(),
            analog_groups=self.task_group_repo.get_list_analog_groups(),
            sources=self.task_catalog_repo.get_list_sources(),
            subtopics=self.task_catalog_repo.get_subtopics_for_topic(
                filters.topic_id,
            ),
            task_types=self.task_catalog_repo.get_task_type_choices(),
            difficulties=[
                (1, 'Базовый'),
                (2, 'Повышенный'),
                (3, 'Высокий'),
            ],
            grade_choices=[(grade, f'{grade} класс') for grade in range(7, 12)],
            total_tasks=self.task_repo.count_tasks(),
            ungrouped_count=self.task_repo.count_ungrouped_tasks(),
            cache_stats=(
                self.math_status_cache.get_cache_stats()
                if include_cache_stats
                else None
            ),
        )
