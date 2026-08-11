"""Django command adapter for task groups and memberships."""

from typing import List

from core_logic.interfaces.task_group_management_repo import (
    ITaskGroupManagementRepository,
)
from core_logic.value_objects.task_print_settings import TASK_BANK_ROLE_CONTROL
from task_groups.models import AnalogGroup, TaskGroup
from tasks.models import Task


class DjangoTaskGroupManagementRepository(ITaskGroupManagementRepository):
    def analog_group_name_exists(self, name: str) -> bool:
        return AnalogGroup.objects.filter(name=name).exists()

    def create_analog_group(self, name: str, description: str = '') -> str:
        group = AnalogGroup.objects.create(name=name, description=description)
        return str(group.pk)

    def update_analog_group(
        self,
        group_id: str,
        name: str,
        description: str = '',
    ) -> bool:
        return AnalogGroup.objects.filter(pk=group_id).update(
            name=name,
            description=description,
        ) > 0

    def get_analog_group_name(self, group_id: str):
        return AnalogGroup.objects.filter(pk=group_id).values_list(
            'name',
            flat=True,
        ).first()

    def add_tasks_to_group(
        self,
        group_id: str,
        task_ids: List[str],
        bank_role: str = TASK_BANK_ROLE_CONTROL,
    ) -> int:
        created_count = 0
        for task in Task.objects.filter(pk__in=task_ids):
            _, created = TaskGroup.objects.get_or_create(
                task=task,
                group_id=group_id,
                defaults={'bank_role': bank_role},
            )
            if created:
                created_count += 1
        return created_count

    def update_task_group_roles(self, group_id: str, task_roles: dict) -> int:
        updated_count = 0
        for task_id, bank_role in task_roles.items():
            updated_count += TaskGroup.objects.filter(
                group_id=group_id,
                task_id=task_id,
            ).update(bank_role=bank_role)
        return updated_count

    def remove_task_from_group(self, group_id: str, task_id: str) -> int:
        return TaskGroup.objects.filter(
            group_id=group_id,
            task_id=task_id,
        ).delete()[0]

    def remove_tasks_from_all_groups(self, task_ids: List[str]) -> int:
        if not task_ids:
            return 0
        return TaskGroup.objects.filter(task_id__in=task_ids).delete()[0]

    def delete_groups(self, group_ids: List[str]) -> int:
        if not group_ids:
            return 0

        groups = AnalogGroup.objects.filter(pk__in=group_ids)
        deleted_count = groups.count()
        groups.delete()
        return deleted_count
