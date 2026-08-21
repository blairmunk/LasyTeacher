"""Validate task import JSON structure."""

from dataclasses import dataclass
from uuid import UUID

from core_logic.entities.core import ImportJsonValidationData
from core_logic.value_objects.task_print_settings import (
    validate_task_specific_bank_role,
)
from core_logic.value_objects.task_transfer_format import (
    task_transfer_format_error,
    task_transfer_format_warning,
)


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

        version_error = task_transfer_format_error(data)
        if version_error:
            return ImportJsonValidationData(
                is_valid=False,
                errors=[version_error],
            )
        version_warning = task_transfer_format_warning(data)
        if version_warning:
            warnings.append(version_warning)

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
        sources_data = data.get('sources', [])

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
        source_uuids = self._validate_sources(sources_data, errors)
        self._validate_task_group_links(
            tasks,
            group_uuids,
            errors,
            warnings,
        )
        self._validate_task_source_links(
            tasks,
            source_uuids,
            errors,
            warnings,
        )

        summary = {
            'tasks_total': len(tasks),
            'tasks_valid': tasks_ok,
            'tasks_errors': tasks_errors,
            'groups_total': len(groups_data),
            'topics_total': len(topics_data),
            'images_total': len(images_data),
            'sources_total': len(sources_data),
        }

        return ImportJsonValidationData(
            is_valid=not errors,
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

        if task.get('content_element') or task.get('requirement_element'):
            task_errors.append(
                f'Задание #{task_number}: используются legacy-поля '
                'content_element/requirement_element; укажите '
                'codifier_content_entries/codifier_requirements',
            )

        self._validate_classifications(
            task,
            task_number,
            task_errors,
        )

        return task_errors

    @staticmethod
    def _validate_classifications(task, task_number, errors):
        for field_name in (
            'codifier_content_entries',
            'codifier_requirements',
        ):
            references = task.get(field_name)
            if references is None:
                continue
            if not isinstance(references, list):
                errors.append(
                    f'Задание #{task_number}: {field_name} должен быть массивом',
                )
                continue
            for index, reference in enumerate(references, start=1):
                if not isinstance(reference, dict):
                    errors.append(
                        f'Задание #{task_number}: {field_name}[{index}] '
                        'должен быть объектом',
                    )
                    continue
                missing = [
                    key
                    for key in ('subject', 'exam_type', 'year', 'code')
                    if reference.get(key) in (None, '')
                ]
                if missing:
                    errors.append(
                        f'Задание #{task_number}: {field_name}[{index}] '
                        f'не содержит {", ".join(missing)}',
                    )

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

    @staticmethod
    def _validate_sources(sources_data, errors):
        if not isinstance(sources_data, list):
            errors.append('"sources" должен быть массивом')
            return set()

        source_uuids = set()
        for index, source in enumerate(sources_data, start=1):
            if not isinstance(source, dict):
                errors.append(f'Источник #{index}: должен быть объектом')
                continue
            if not source.get('name'):
                errors.append(f'Источник #{index}: отсутствует name')

            source_uuid = source.get('id') or source.get('uuid')
            if not source_uuid:
                errors.append(
                    f'Источник #{index}: отсутствует id (UUID)',
                )
                continue
            try:
                normalized_uuid = str(UUID(str(source_uuid)))
            except (TypeError, ValueError):
                errors.append(
                    f'Источник #{index}: некорректный UUID '
                    f'"{source_uuid}"',
                )
                continue
            if normalized_uuid in source_uuids:
                errors.append(
                    f'Источник #{index}: дублирующийся id {source_uuid}',
                )
            source_uuids.add(normalized_uuid)
        return source_uuids

    @staticmethod
    def _validate_task_source_links(tasks, source_uuids, errors, warnings):
        for index, task in enumerate(tasks, start=1):
            if not isinstance(task, dict) or not task.get('source'):
                continue
            source_ref = task['source']
            if not isinstance(source_ref, dict):
                errors.append(
                    f'Задание #{index}: source должен быть '
                    'объектом с id (UUID)',
                )
                continue
            source_uuid = source_ref.get('id') or source_ref.get('uuid')
            if not source_uuid:
                errors.append(
                    f'Задание #{index}: у source отсутствует id (UUID)',
                )
                continue
            try:
                normalized_uuid = str(UUID(str(source_uuid)))
            except (TypeError, ValueError):
                errors.append(
                    f'Задание #{index}: у source некорректный UUID '
                    f'"{source_uuid}"',
                )
                continue
            if normalized_uuid not in source_uuids:
                warnings.append(
                    f'Задание #{index}: ссылка на источник '
                    f'{normalized_uuid[-8:]}... не найдена в sources '
                    '(будет искать в БД)',
                )

    def _validate_task_group_links(
        self,
        tasks,
        group_uuids,
        errors,
        warnings,
    ):
        for index, task in enumerate(tasks):
            if not isinstance(task, dict):
                continue
            for group_ref in task.get('groups', []):
                group_uuid = self._group_reference_id(
                    group_ref,
                    task_number=index + 1,
                    errors=errors,
                )
                if not group_uuid:
                    continue
                if group_uuid not in group_uuids:
                    warnings.append(
                        f'Задание #{index + 1}: ссылка на группу {group_uuid[-8:]}... '
                        f'не найдена в analog_groups (будет искать в БД)',
                    )

    @staticmethod
    def _group_reference_id(group_ref, task_number, errors):
        if isinstance(group_ref, str):
            return group_ref
        if not isinstance(group_ref, dict):
            errors.append(
                f'Задание #{task_number}: связь с группой '
                'должна быть UUID-строкой или объектом',
            )
            return ''

        group_uuid = group_ref.get('id') or group_ref.get('group_id') or ''
        if not group_uuid:
            errors.append(
                f'Задание #{task_number}: у связи с группой '
                'отсутствует id',
            )
        try:
            validate_task_specific_bank_role(
                group_ref.get('bank_role', 'control'),
            )
        except ValueError as error:
            errors.append(f'Задание #{task_number}: {error}')
        return group_uuid
