"""Task group wiring for the dependency container."""

from core_logic.use_cases.bulk_change_task_groups import (
    BulkAddTasksToGroupUseCase,
    BulkCreateGroupFromTasksUseCase,
    BulkRemoveTasksFromGroupsUseCase,
)
from core_logic.use_cases.change_task_group_membership import (
    AddTasksToGroupUseCase,
    RemoveTaskFromGroupUseCase,
    UpdateTaskGroupRolesUseCase,
)
from core_logic.use_cases.delete_task_groups import DeleteTaskGroupsUseCase
from core_logic.use_cases.get_add_tasks_to_group import GetAddTasksToGroupUseCase
from core_logic.use_cases.get_task_group_detail import GetTaskGroupDetailUseCase
from core_logic.use_cases.get_task_group_list import GetTaskGroupListUseCase
from core_logic.use_cases.prepare_task_group_membership_submission import (
    PrepareAddTasksToGroupSubmissionUseCase,
    PrepareUpdateTaskGroupRolesSubmissionUseCase,
)
from core_logic.use_cases.save_analog_group import (
    CreateAnalogGroupUseCase,
    UpdateAnalogGroupUseCase,
)
from infrastructure.forms.task_group_forms import TaskGroupFormAdapter
from infrastructure.repositories.django_task_group_catalog_repo import (
    DjangoTaskGroupCatalogRepository,
)
from infrastructure.repositories.django_task_group_management_repo import (
    DjangoTaskGroupManagementRepository,
)


class TaskGroupCompositionMixin:
    """Owns analog groups and task group membership wiring."""

    def _initialize_task_group_composition(self):
        self._task_group_catalog_repo = None
        self._task_group_management_repo = None
        self._task_group_form_adapter = None

    @property
    def task_group_catalog_repo(self):
        if self._task_group_catalog_repo is None:
            self._task_group_catalog_repo = DjangoTaskGroupCatalogRepository()
        return self._task_group_catalog_repo

    @property
    def task_group_management_repo(self):
        if self._task_group_management_repo is None:
            self._task_group_management_repo = (
                DjangoTaskGroupManagementRepository()
            )
        return self._task_group_management_repo

    @property
    def task_group_form_adapter(self):
        if self._task_group_form_adapter is None:
            self._task_group_form_adapter = TaskGroupFormAdapter()
        return self._task_group_form_adapter

    def get_task_group_list_use_case(self):
        return GetTaskGroupListUseCase(
            task_catalog_repo=self.task_taxonomy_repo,
            task_group_repo=self.task_group_catalog_repo,
        )

    def get_task_group_detail_use_case(self):
        return GetTaskGroupDetailUseCase(
            task_group_repo=self.task_group_catalog_repo,
        )

    def create_analog_group_use_case(self):
        return CreateAnalogGroupUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def update_analog_group_use_case(self):
        return UpdateAnalogGroupUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def get_add_tasks_to_group_use_case(self):
        return GetAddTasksToGroupUseCase(
            task_group_repo=self.task_group_catalog_repo,
        )

    def prepare_add_tasks_to_group_submission_use_case(self):
        return PrepareAddTasksToGroupSubmissionUseCase()

    def prepare_update_task_group_roles_submission_use_case(self):
        return PrepareUpdateTaskGroupRolesSubmissionUseCase()

    def delete_task_groups_use_case(self):
        return DeleteTaskGroupsUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def add_tasks_to_group_use_case(self):
        return AddTasksToGroupUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def remove_task_from_group_use_case(self):
        return RemoveTaskFromGroupUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def update_task_group_roles_use_case(self):
        return UpdateTaskGroupRolesUseCase(
            task_group_repo=self.task_group_management_repo,
        )

    def bulk_create_group_from_tasks_use_case(self):
        return BulkCreateGroupFromTasksUseCase(
            task_repo=self.task_selection_repo,
            task_group_repo=self.task_group_management_repo,
        )

    def bulk_add_tasks_to_group_use_case(self):
        return BulkAddTasksToGroupUseCase(
            task_repo=self.task_selection_repo,
            task_group_repo=self.task_group_management_repo,
        )

    def bulk_remove_tasks_from_groups_use_case(self):
        return BulkRemoveTasksFromGroupsUseCase(
            task_group_repo=self.task_group_management_repo,
        )
