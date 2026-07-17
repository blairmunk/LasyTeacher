"""Validate task import JSON structure."""

from dataclasses import dataclass
from uuid import UUID

from core_logic.entities.core import ImportJsonValidationData


@dataclass(frozen=True)
class ValidateTaskImportJsonRequest:
    data: object


class ValidateTaskImportJsonUseCase:
    def execute(
        self,
        request: ValidateTaskImportJsonRequest,
    ) -> ImportJsonValidationData:
        data = request.data
        errors = []
        warnings = []
        summary = {}

        if not isinstance(data, dict):
            return ImportJsonValidationData(
                is_valid=False,
                errors=['Корневой элемент должен быть объектом {}'],
            )

        if 'tasks' not in data:
            return ImportJsonValidationData(
                is_valid=False,
                errors=['Отсутствует обязательное поле "tasks"'],
            )

        tasks = data['tasks']
        if not isinstance(tasks, list):
            return ImportJsonValidationData(
                is_valid=False,
                errors=['"tasks" должен быть массивом'],
            )

        if len(tasks) == 0:
            warnings.append('Массив "tasks" пуст')

        groups_data = data.get('analog_groups', [])
        topics_data = data.get('topics', [])
        images_data = data.get('task_images', [])

        tasks_ok = 0
        tasks_errors = 0
        uuids_seen = set()

        for index, task in enumerate(tasks):
            task_errors = self._validate_task(
                task=task,
                index=index,
                uuids_seen=uuids_seen,
                warnings=warnings,
            )

            if task_errors:
                errors.extend(task_errors)
                tasks_errors += 1
            else:
                tasks_ok += 1

        group_uuids = self._validate_groups(groups_data, errors)
        self._validate_task_group_links(tasks, group_uuids, warnings)

        summary = {
            'tasks_total': len(tasks),
            'tasks_valid': tasks_ok,
            'tasks_errors': tasks_errors,
            'groups_total': len(groups_data),
            'topics_total': len(topics_data),
            'images_total': len(images_data),
        }

        return ImportJsonValidationData(
            is_valid=tasks_errors == 0,
            errors=errors,
            warnings=warnings,
            summary=summary,
        )

    def _validate_task(self, task, index, uuids_seen, warnings):
        task_errors = []
        task_number = index + 1

        if not isinstance(task, dict):
            return [f'Задание #{task_number}: должно быть объектом']

        task_uuid = task.get('id')
        if not task_uuid:
            task_errors.append(f'Задание #{task_number}: отсутствует id (UUID)')
        elif task_uuid in uuids_seen:
            task_errors.append(f'Задание #{task_number}: дублирующийся id {task_uuid}')
        else:
            try:
                UUID(task_uuid)
                uuids_seen.add(task_uuid)
            except ValueError:
                task_errors.append(
                    f'Задание #{task_number}: некорректный UUID "{task_uuid}"',
                )

        if not task.get('text'):
            task_errors.append(f'Задание #{task_number}: отсутствует text')

        if not task.get('answer'):
            warnings.append(f'Задание #{task_number}: нет ответа')
        if not task.get('topic'):
            warnings.append(f'Задание #{task_number}: нет темы')
        if not task.get('groups') and not task.get('group_name'):
            warnings.append(f'Задание #{task_number}: нет привязки к группе')

        return task_errors

    def _validate_groups(self, groups_data, errors):
        group_uuids = set()

        for index, group in enumerate(groups_data):
            group_number = index + 1
            if not isinstance(group, dict):
                errors.append(f'Группа #{group_number}: должна быть объектом')
                continue
            if not group.get('id'):
                errors.append(f'Группа #{group_number}: отсутствует id (UUID)')
            else:
                group_uuids.add(group['id'])
            if not group.get('name'):
                errors.append(f'Группа #{group_number}: отсутствует name')

        return group_uuids

    def _validate_task_group_links(self, tasks, group_uuids, warnings):
        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue
            for group_uuid in task.get('groups', []):
                if group_uuid not in group_uuids:
                    warnings.append(
                        f'Задание #{index + 1}: ссылка на группу {group_uuid[-8:]}... '
                        f'не найдена в analog_groups (будет искать в БД)',
                    )
