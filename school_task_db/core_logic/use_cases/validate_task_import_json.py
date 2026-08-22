"""Validate task import JSON structure."""

from dataclasses import dataclass

from core_logic.entities.core import ImportJsonValidationData
from core_logic.services.task_import_image_validation_service import (
    TaskImportImageValidationService,
)
from core_logic.value_objects.task_import import (
    normalize_task_import_uuid,
    parse_task_group_import_reference,
)
from core_logic.value_objects.task_transfer_format import (
    task_transfer_format_error,
    task_transfer_format_warning,
)


@dataclass(frozen=True)
class ValidateTaskImportJsonRequest:
    data: object


class ValidateTaskImportJsonUseCase:
    def __init__(self, image_validation_service=None):
        self.image_validation_service = (
            image_validation_service or TaskImportImageValidationService()
        )

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

        image_validation = self.image_validation_service.validate(
            images_data,
            declared_task_ids=uuids_seen,
        )
        errors.extend(image_validation.errors)
        warnings.extend(image_validation.warnings)

        group_uuids = self._validate_groups(groups_data, errors)
        source_uuids = self._validate_sources(sources_data, errors)
        topic_uuids, subtopic_topics = self._validate_topics(
            topics_data,
            errors,
        )
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
        self._validate_task_topic_links(
            tasks,
            topic_uuids,
            subtopic_topics,
            errors,
            warnings,
        )

        summary = {
            'tasks_total': len(tasks),
            'tasks_valid': tasks_ok,
            'tasks_errors': tasks_errors,
            'groups_total': len(groups_data),
            'topics_total': len(topics_data),
            'images_total': image_validation.total,
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
        else:
            try:
                normalized_uuid = normalize_task_import_uuid(task_uuid)
            except ValueError:
                task_errors.append(
                    f'Задание #{task_number}: некорректный UUID "{task_uuid}"',
                )
            else:
                if normalized_uuid in uuids_seen:
                    task_errors.append(
                        f'Задание #{task_number}: '
                        f'дублирующийся id {task_uuid}',
                    )
                uuids_seen.add(normalized_uuid)

        if not task.get('text'):
            task_errors.append(f'Задание #{task_number}: отсутствует text')

        if not task.get('answer'):
            warnings.append(f'Задание #{task_number}: нет ответа')
        if not task.get('topic'):
            warnings.append(f'Задание #{task_number}: нет темы')
        if not task.get('groups'):
            warnings.append(f'Задание #{task_number}: нет привязки к группе')
        if task.get('group_name'):
            task_errors.append(
                f'Задание #{task_number}: legacy-поле group_name '
                'не поддерживается; укажите groups с UUID',
            )

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
        if not isinstance(groups_data, list):
            errors.append('"analog_groups" должен быть массивом')
            return set()
        group_uuids = set()

        for index, group in enumerate(groups_data):
            group_number = index + 1
            if not isinstance(group, dict):
                errors.append(f'Группа #{group_number}: должна быть объектом')
                continue
            if not group.get('id'):
                errors.append(f'Группа #{group_number}: отсутствует id (UUID)')
            else:
                try:
                    group_uuid = normalize_task_import_uuid(group['id'])
                except ValueError:
                    errors.append(
                        f'Группа #{group_number}: некорректный '
                        f'UUID "{group["id"]}"',
                    )
                else:
                    if group_uuid in group_uuids:
                        errors.append(
                            f'Группа #{group_number}: дублирующийся '
                            f'id {group["id"]}',
                        )
                    group_uuids.add(group_uuid)
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
                normalized_uuid = normalize_task_import_uuid(source_uuid)
            except ValueError:
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
    def _validate_topics(topics_data, errors):
        if not isinstance(topics_data, list):
            errors.append('"topics" должен быть массивом')
            return set(), {}

        topic_uuids = set()
        subtopic_topics = {}
        for index, topic in enumerate(topics_data, start=1):
            if not isinstance(topic, dict):
                errors.append(f'Тема #{index}: должна быть объектом')
                continue
            topic_uuid = ValidateTaskImportJsonUseCase._catalog_uuid(
                topic,
                label=f'Тема #{index}',
                seen=topic_uuids,
                errors=errors,
            )
            for field_name in ('name', 'subject', 'grade_level'):
                if topic.get(field_name) in (None, ''):
                    errors.append(
                        f'Тема #{index}: отсутствует {field_name}',
                    )

            subtopics = topic.get('subtopics', [])
            if not isinstance(subtopics, list):
                errors.append(
                    f'Тема #{index}: subtopics должен быть массивом',
                )
                continue
            for subtopic_index, subtopic in enumerate(subtopics, start=1):
                label = f'Тема #{index}, подтема #{subtopic_index}'
                if not isinstance(subtopic, dict):
                    errors.append(f'{label}: должна быть объектом')
                    continue
                subtopic_uuid = ValidateTaskImportJsonUseCase._catalog_uuid(
                    subtopic,
                    label=label,
                    seen=set(subtopic_topics),
                    errors=errors,
                )
                if not subtopic.get('name'):
                    errors.append(f'{label}: отсутствует name')
                if subtopic_uuid and topic_uuid:
                    subtopic_topics[subtopic_uuid] = topic_uuid
        return topic_uuids, subtopic_topics

    @staticmethod
    def _catalog_uuid(data, *, label, seen, errors):
        value = data.get('id') or data.get('uuid')
        if not value:
            errors.append(f'{label}: отсутствует id (UUID)')
            return ''
        try:
            normalized = normalize_task_import_uuid(value)
        except ValueError:
            errors.append(f'{label}: некорректный UUID "{value}"')
            return ''
        if normalized in seen:
            errors.append(f'{label}: дублирующийся id {value}')
            return ''
        seen.add(normalized)
        return normalized

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
                normalized_uuid = normalize_task_import_uuid(source_uuid)
            except ValueError:
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

    @staticmethod
    def _validate_task_topic_links(
        tasks,
        topic_uuids,
        subtopic_topics,
        errors,
        warnings,
    ):
        for index, task in enumerate(tasks, start=1):
            if not isinstance(task, dict):
                continue
            topic_uuid = ValidateTaskImportJsonUseCase._task_reference_uuid(
                task.get('topic'),
                label=f'Задание #{index}: topic',
                errors=errors,
            )
            if topic_uuid and topic_uuid not in topic_uuids:
                warnings.append(
                    f'Задание #{index}: ссылка на тему '
                    f'{topic_uuid[-8:]}... не найдена в topics '
                    '(будет искать в БД)',
                )

            subtopic_ref = task.get('subtopic')
            if not subtopic_ref:
                continue
            subtopic_uuid = ValidateTaskImportJsonUseCase._task_reference_uuid(
                subtopic_ref,
                label=f'Задание #{index}: subtopic',
                errors=errors,
            )
            if not subtopic_uuid:
                continue
            if not topic_uuid:
                errors.append(
                    f'Задание #{index}: subtopic указан без '
                    'корректной topic',
                )
                continue
            declared_topic_uuid = subtopic_topics.get(subtopic_uuid)
            if declared_topic_uuid and declared_topic_uuid != topic_uuid:
                errors.append(
                    f'Задание #{index}: подтема {subtopic_uuid[-8:]} '
                    'принадлежит другой теме',
                )
            elif not declared_topic_uuid:
                warnings.append(
                    f'Задание #{index}: ссылка на подтему '
                    f'{subtopic_uuid[-8:]}... не найдена в topics '
                    '(будет искать в БД)',
                )

    @staticmethod
    def _task_reference_uuid(reference, *, label, errors):
        if reference in (None, ''):
            return ''
        if not isinstance(reference, dict):
            errors.append(
                f'{label} должен быть объектом с id (UUID)',
            )
            return ''
        value = reference.get('id') or reference.get('uuid')
        if not value:
            errors.append(f'{label}: отсутствует id (UUID)')
            return ''
        try:
            return normalize_task_import_uuid(value)
        except ValueError:
            errors.append(f'{label}: некорректный UUID "{value}"')
            return ''

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
        try:
            reference = parse_task_group_import_reference(group_ref)
        except ValueError as error:
            errors.append(
                f'Задание #{task_number}: {error}',
            )
            return ''
        return reference.group_id
