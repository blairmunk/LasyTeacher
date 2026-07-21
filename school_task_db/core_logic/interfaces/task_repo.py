"""Task repository interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Set, Tuple

from core_logic.entities.task import (
    AddTasksToGroupTask,
    ReferenceElementOption,
    SelectOption,
    SourceCreateParams,
    SourceCreateResult,
    SourceListItem,
    TaskEntity,
    TaskExportFilters,
    TaskGroupDetailGroup,
    TaskGroupDetailTask,
    TaskGroupListItem,
    TaskGroupListFilters,
    TaskDetailGroup,
    TaskDetailTask,
    TaskListItem,
    TaskListFilters,
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskSaveParams,
    TaskSaveResult,
)
from core_logic.value_objects.variant_print_plan import TASK_BANK_ROLE_CONTROL


class ITaskRepository(ABC):
    @abstractmethod
    def get_list_tasks(self, filters: TaskListFilters) -> List[TaskListItem]:
        """Return tasks for the task list page."""

    @abstractmethod
    def get_list_task_groups(self, filters: TaskGroupListFilters) -> List[TaskGroupListItem]:
        """Return analog groups for the analog group list page."""

    @abstractmethod
    def get_analog_group_detail(self, group_id: str) -> Optional[TaskGroupDetailGroup]:
        """Return one analog group detail read model, or None."""

    @abstractmethod
    def get_task_group_detail_tasks(
        self,
        group_id: str,
    ) -> List[TaskGroupDetailTask]:
        """Return task read models for one analog group detail page."""

    @abstractmethod
    def get_analog_group(self, group_id: str) -> Any:
        """Return one analog group, or None when it does not exist."""

    @abstractmethod
    def get_available_tasks_for_analog_group(
        self,
        group_id: str,
        search: str,
    ) -> List[AddTasksToGroupTask]:
        """Return tasks not yet assigned to one analog group."""

    @abstractmethod
    def get_task(self, task_id: str) -> Optional[TaskDetailTask]:
        """Return one task detail read model, or None when it does not exist."""

    @abstractmethod
    def create_task(self, params: TaskSaveParams) -> TaskSaveResult:
        """Create a task."""

    @abstractmethod
    def update_task(self, params: TaskSaveParams) -> TaskSaveResult:
        """Update a task, or return not_found status."""

    @abstractmethod
    def save_task_images(
        self,
        task_id: str,
        images: List[TaskImageSaveParams],
    ) -> TaskImagesSaveResult:
        """Persist task images and return change counts."""

    @abstractmethod
    def get_task_detail_groups(self, task_id: str) -> List[TaskDetailGroup]:
        """Return analog-group read models for one task detail page."""

    @abstractmethod
    def get_list_topics(self) -> Any:
        """Return topic options for the task list page."""

    @abstractmethod
    def get_list_analog_groups(self) -> Any:
        """Return analog-group options for the task list page."""

    @abstractmethod
    def count_analog_groups(self) -> int:
        """Return total analog group count."""

    @abstractmethod
    def count_empty_analog_groups(self) -> int:
        """Return analog groups without tasks."""

    @abstractmethod
    def count_task_group_memberships(self) -> int:
        """Return total task-to-group memberships."""

    @abstractmethod
    def get_list_sources(self) -> Any:
        """Return source options for the task list page."""

    @abstractmethod
    def build_task_export_payload(
        self,
        filters: TaskExportFilters,
        export_date: str,
    ) -> dict:
        """Return TaskImporter-compatible task export payload."""

    @abstractmethod
    def get_source_list_sources(self) -> List[SourceListItem]:
        """Return sources for the source list page."""

    @abstractmethod
    def create_source(self, params: SourceCreateParams) -> SourceCreateResult:
        """Create a task source and return its read model."""

    @abstractmethod
    def get_subtopics_for_topic(self, topic_id: str) -> Any:
        """Return subtopic options for a topic."""

    @abstractmethod
    def get_subtopic_options(self, topic_id: str) -> List[SelectOption]:
        """Return subtopic select options for a topic."""

    @abstractmethod
    def get_reference_element_options(
        self,
        subject: str,
        category: str,
    ) -> List[ReferenceElementOption]:
        """Return codifier reference element options."""

    @abstractmethod
    def get_task_type_choices(self) -> List[Tuple[str, str]]:
        """Return task type choices."""

    @abstractmethod
    def count_tasks(self) -> int:
        """Return total task count."""

    @abstractmethod
    def count_ungrouped_tasks(self) -> int:
        """Return task count without analog groups."""

    @abstractmethod
    def get_math_cache_stats(self) -> Any:
        """Return math cache stats for task administration UI."""

    @abstractmethod
    def refresh_math_cache(self) -> dict:
        """Refresh task math cache and return grouped task IDs."""

    @abstractmethod
    def get_by_ids(self, task_ids: Set[str]) -> List[TaskEntity]:
        """Return tasks by IDs."""

    @abstractmethod
    def get_group_ids_for_tasks(self, task_ids: Set[str]) -> Set[str]:
        """Return analog-group IDs containing the given tasks."""

    @abstractmethod
    def count_existing_task_ids(self, task_ids: Set[str]) -> int:
        """Return how many tasks from the given IDs exist."""

    @abstractmethod
    def count_existing_group_ids(self, group_ids: Set[str]) -> int:
        """Return how many analog groups from the given IDs exist."""

    @abstractmethod
    def analog_group_name_exists(self, name: str) -> bool:
        """Return whether an analog group with the given name exists."""

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
    def get_first_task_difficulty_for_group(self, group_id: str) -> int:
        """Return the first task difficulty for an analog group, or 1."""

    @abstractmethod
    def get_analog_group_name(self, group_id: str) -> Optional[str]:
        """Return an analog-group name, or None when it does not exist."""

    @abstractmethod
    def add_tasks_to_group(
        self,
        group_id: str,
        task_ids: List[str],
        bank_role: str = TASK_BANK_ROLE_CONTROL,
    ) -> int:
        """Add tasks to an analog group and return created membership count."""

    @abstractmethod
    def update_task_group_roles(
        self,
        group_id: str,
        task_roles: Dict[str, str],
    ) -> int:
        """Update bank roles for existing task memberships in one analog group."""

    @abstractmethod
    def remove_task_from_group(self, group_id: str, task_id: str) -> int:
        """Remove one task from an analog group and return deleted row count."""

    @abstractmethod
    def remove_tasks_from_all_groups(self, task_ids: List[str]) -> int:
        """Remove selected tasks from all analog groups and return deleted count."""

    @abstractmethod
    def delete_task(self, task_id: str) -> int:
        """Delete one task and return deleted object count."""

    @abstractmethod
    def delete_groups(self, group_ids: List[str]) -> int:
        """Delete analog groups by IDs and return deleted object count."""

    @abstractmethod
    def get_tasks_in_group(self, group_id: str) -> Set[str]:
        """Return all task IDs in an analog group."""

    @abstractmethod
    def get_tasks_by_difficulty(
        self,
        task_ids: Set[str],
        max_difficulty: int,
    ) -> List[TaskEntity]:
        """Return tasks from task_ids with difficulty not greater than max_difficulty."""
