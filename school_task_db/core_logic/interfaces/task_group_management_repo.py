"""Command port for managing task groups and their memberships."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from core_logic.value_objects.task_print_settings import TASK_BANK_ROLE_CONTROL


class ITaskGroupManagementRepository(ABC):
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
