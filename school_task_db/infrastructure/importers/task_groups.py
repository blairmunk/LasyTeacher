"""Django analog-group import and task membership handling."""

from core_logic.value_objects.task_import import (
    parse_task_group_import_reference,
)
from task_groups.models import AnalogGroup, TaskGroup


class TaskGroupImporter:
    def __init__(self, runtime, registry):
        self.runtime = runtime
        self.registry = registry

    def import_groups(self, groups_data):
        self.runtime.write('📋 Импорт групп аналогов...')
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
        group_uuid = group_data['id']
        group = self.find_by_uuid(group_uuid)
        if group and not self.runtime.should_create_object(
            group,
            group_data,
            'groups',
        ):
            if self.runtime.mode == 'update':
                self._update_group(group, group_data)
                self.runtime.stats.record_updated('groups', group.pk)
            self.registry.remember_group(group_uuid, group)
            return
        if group:
            return

        group = AnalogGroup.objects.create(
            id=group_uuid,
            name=group_data['name'],
            description=group_data.get('description', ''),
            difficulty=group_data.get('difficulty', 0),
        )
        self.registry.remember_group(group_uuid, group)
        self.runtime.stats.record_created('groups', group.pk)
        self.runtime.log_success(
            f'Создана группа: {group.name} [{group.get_short_uuid()}]',
        )

    def create_task_relations(self, tasks_data):
        self.runtime.write('🔗 Создание связей заданий с группами...')
        created_count = 0
        for task_data in tasks_data:
            task_uuid = task_data.get('id')
            task = self.registry.task(task_uuid)
            if not task:
                continue

            for group_ref in task_data.get('groups', []):
                try:
                    reference = parse_task_group_import_reference(group_ref)
                except ValueError as error:
                    self.runtime.log_warning(
                        f'Пропущена связь задания {task_uuid[-8:]} '
                        f'с группой: {error}',
                    )
                    continue
                group = (
                    self.registry.group(reference.group_id)
                    or self.find_by_uuid(reference.group_id)
                )
                if group and self._save_relation(
                    task,
                    group,
                    reference.bank_role,
                ):
                    created_count += 1

        self.runtime.write(f'  ✅ Создано связей: {created_count}')

    def find_by_uuid(self, group_uuid):
        return self.runtime.get_by_uuid(AnalogGroup, group_uuid)

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
