"""Analog task group repository interface."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from core_logic.entities.task import (
    AddTasksToGroupTask,
    SelectOption,
    TaskGroupDetailGroup,
    TaskGroupDetailTask,
    TaskGroupListFilters,
    TaskGroupListItem,
)
from core_logic.value_objects.task_print_settings import TASK_BANK_ROLE_CONTROL


class ITaskGroupRepository(ABC):
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

    @abstractmethod
    def analog_group_name_exists(self, name: str) -> bool:
        """Return whether an analog group name is already used."""

    @abstractmethod
    def create_analog_group(self, name: str, description: str = '') -> str:
        """Create an analog group and return its ID."""

    @abstractmethod
    def update_analog_group(
        self,
        group_id: str,
        name: str,
        description: str = '',
    ) -> bool:
        """Update an analog group and return whether it existed."""

    @abstractmethod
    def get_analog_group_name(self, group_id: str) -> Optional[str]:
        """Return an analog-group name, or None."""

    @abstractmethod
    def add_tasks_to_group(
        self,
        group_id: str,
        task_ids: List[str],
        bank_role: str = TASK_BANK_ROLE_CONTROL,
    ) -> int:
        """Add tasks to a group and return created membership count."""

    @abstractmethod
    def update_task_group_roles(
        self,
        group_id: str,
        task_roles: Dict[str, str],
    ) -> int:
        """Update roles for existing task memberships."""

    @abstractmethod
    def remove_task_from_group(self, group_id: str, task_id: str) -> int:
        """Remove one task membership and return deleted row count."""

    @abstractmethod
    def remove_tasks_from_all_groups(self, task_ids: List[str]) -> int:
        """Remove selected tasks from every group."""

    @abstractmethod
    def delete_groups(self, group_ids: List[str]) -> int:
        """Delete analog groups and return deleted group count."""
