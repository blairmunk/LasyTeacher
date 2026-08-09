"""Django analog-group import and task membership handling."""

from typing import Any

from core_logic.value_objects.task_print_settings import (
    TASK_BANK_ROLE_CONTROL,
    validate_task_specific_bank_role,
)
from task_groups.models import AnalogGroup, TaskGroup


class TaskGroupImporter:
    def __init__(self, runtime, context):
        self.runtime = runtime
        self.context = context

    def import_groups(self, groups_data):
        self.runtime._write('📋 Импорт групп аналогов...')
        for group_data in groups_data:
            try:
                self._import_group(group_data)
            except Exception as error:
                name = group_data.get('name', 'Unknown')
                self.runtime.log_error(
                    f'Ошибка импорта группы {name}: {error}',
                    error,
                )

    def _import_group(self, group_data):
        group_uuid = self.runtime.generate_uuid_if_missing(group_data, 'id')
        group = self.find_by_uuid(group_uuid)
        if group and not self.runtime.should_create_object(group, group_data):
            if self.runtime.mode == 'update':
                self._update_group(group, group_data)
                self.runtime.stats.updated += 1
            self.context.add_group(group_uuid, group)
            return
        if group:
            return

        group = AnalogGroup.objects.create(
            id=group_uuid,
            name=group_data['name'],
            description=group_data.get('description', ''),
            difficulty=group_data.get('difficulty', 0),
        )
        self.context.add_group(group_uuid, group)
        self.runtime.stats.created += 1
        self.runtime.log_success(
            f'Создана группа: {group.name} [{group.get_short_uuid()}]',
        )

    def create_task_relations(self, tasks_data):
        self.runtime._write('🔗 Создание связей заданий с группами...')
        created_count = 0
        for task_data in tasks_data:
            task_uuid = task_data.get('id')
            task = self.context.imported_tasks.get(task_uuid)
            if not task:
                continue

            for group_ref in task_data.get('groups', []):
                group_uuid, bank_role = self.parse_reference(group_ref)
                if not group_uuid:
                    self.runtime.log_warning(
                        f'Пропущена связь задания {task_uuid[-8:]} '
                        'с группой без id',
                    )
                    continue
                group = (
                    self.context.imported_groups.get(group_uuid)
                    or self.find_by_uuid(group_uuid)
                )
                if group and self._save_relation(task, group, bank_role):
                    created_count += 1

            group_name = task_data.get('group_name')
            if group_name and not task_data.get('groups'):
                group = self._get_or_create_by_name(group_name)
                if group and self._save_relation(
                    task,
                    group,
                    TASK_BANK_ROLE_CONTROL,
                ):
                    created_count += 1

        self.runtime._write(f'  ✅ Создано связей: {created_count}')

    @staticmethod
    def parse_reference(group_ref: Any):
        if isinstance(group_ref, str):
            return group_ref, TASK_BANK_ROLE_CONTROL
        if isinstance(group_ref, dict):
            bank_role = group_ref.get('bank_role', TASK_BANK_ROLE_CONTROL)
            validate_task_specific_bank_role(bank_role)
            return (
                group_ref.get('id') or group_ref.get('group_id') or '',
                bank_role,
            )
        return '', TASK_BANK_ROLE_CONTROL

    def find_by_uuid(self, group_uuid):
        return self.runtime.safe_get_by_uuid(AnalogGroup, group_uuid)

    @staticmethod
    def exists_by_name(group_name):
        return AnalogGroup.objects.filter(name=group_name).exists()

    def _get_or_create_by_name(self, group_name):
        group = AnalogGroup.objects.filter(name=group_name).first()
        if group or not self.runtime.create_missing:
            return group
        try:
            group = AnalogGroup.objects.create(
                name=group_name,
                description='Автоматически создана при импорте заданий',
            )
            self.runtime.log_success(f'Создана группа: {group_name}')
            return group
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка создания группы {group_name}: {error}',
                error,
            )
            return None

    def _save_relation(self, task, group, bank_role):
        try:
            relation, created = TaskGroup.objects.get_or_create(
                task=task,
                group=group,
                defaults={'bank_role': bank_role},
            )
            if not created and relation.bank_role != bank_role:
                relation.bank_role = bank_role
                relation.save(update_fields=['bank_role', 'updated_at'])
            if created:
                self.runtime.log_info(
                    f'Связь: {task.get_short_uuid()} ↔ '
                    f'{group.get_short_uuid()}',
                )
            return created
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка создания связи: {error}',
                error,
            )
            return False

    def _update_group(self, group, group_data):
        try:
            group.name = group_data.get('name', group.name)
            group.description = group_data.get(
                'description',
                group.description,
            )
            group.difficulty = group_data.get(
                'difficulty',
                group.difficulty,
            )
            group.save()
            self.runtime.log_success(
                f'Обновлена группа: {group.name} '
                f'[{group.get_short_uuid()}]',
            )
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка обновления группы: {error}',
                error,
            )
