"""Read port for task-group catalog pages."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.task import (
    AddTasksToGroupTask,
    SelectOption,
    TaskGroupDetailGroup,
    TaskGroupDetailTask,
    TaskGroupListFilters,
    TaskGroupListItem,
)


class ITaskGroupCatalogRepository(ABC):
    @abstractmethod
    def get_list_task_groups(
        self,
        filters: TaskGroupListFilters,
    ) -> List[TaskGroupListItem]:
        """Return analog groups for the group list page."""

    @abstractmethod
    def get_analog_group_detail(
        self,
        group_id: str,
    ) -> Optional[TaskGroupDetailGroup]:
        """Return one analog group detail read model, or None."""

    @abstractmethod
    def get_task_group_detail_tasks(
        self,
        group_id: str,
    ) -> List[TaskGroupDetailTask]:
        """Return task read models for one analog group."""

    @abstractmethod
    def get_available_tasks_for_analog_group(
        self,
        group_id: str,
        search: str,
    ) -> List[AddTasksToGroupTask]:
        """Return tasks not yet assigned to an analog group."""

    @abstractmethod
    def get_list_analog_groups(self) -> List[SelectOption]:
        """Return analog-group select options."""

    @abstractmethod
    def count_analog_groups(self) -> int:
        """Return total analog group count."""

    @abstractmethod
    def count_empty_analog_groups(self) -> int:
        """Return analog groups without tasks."""

    @abstractmethod
    def count_task_group_memberships(self) -> int:
        """Return total task-to-group membership count."""
