"""Validation of portable task-image records before persistence."""

import base64

from core_logic.entities.task_import import TaskImportImageValidationResult
from core_logic.value_objects.task_image_position import (
    TASK_IMAGE_POSITION_LABELS,
)
from core_logic.value_objects.task_import import normalize_task_import_uuid


class TaskImportImageValidationService:
    def validate(
        self,
        images,
        *,
        declared_task_ids,
    ) -> TaskImportImageValidationResult:
        if not isinstance(images, list):
            return TaskImportImageValidationResult(
                errors=('"task_images" должен быть массивом',),
            )

        errors = []
        warnings = []
        seen_ids = set()
        declared_task_ids = set(declared_task_ids)
        for index, image in enumerate(images, start=1):
            label = f'Изображение #{index}'
            if not isinstance(image, dict):
                errors.append(f'{label}: должно быть объектом')
                continue

            image_id = self._uuid(
                image.get('id'),
                label=label,
                field_name='id',
                errors=errors,
            )
            if image_id:
                if image_id in seen_ids:
                    errors.append(f'{label}: дублирующийся id {image_id}')
                seen_ids.add(image_id)

            raw_task_id = image.get('task_id') or image.get('task_uuid')
            task_id = self._uuid(
                raw_task_id,
                label=label,
                field_name='task_id',
                errors=errors,
            )
            if task_id and task_id not in declared_task_ids:
                errors.append(
                    f'{label}: task_id {task_id[-8:]} не найден '
                    'среди tasks этого файла',
                )

            position = image.get('position', '')
            if position and position not in TASK_IMAGE_POSITION_LABELS:
                errors.append(
                    f'{label}: неподдерживаемая position "{position}"',
                )

            order = image.get('order', 1)
            if not isinstance(order, int) or isinstance(order, bool) or order < 0:
                errors.append(
                    f'{label}: order должен быть '
                    'целым неотрицательным числом',
                )

            encoded = image.get('base64_data')
            if not encoded:
                warnings.append(
                    f'{label}: нет base64_data; '
                    'файл можно не создать',
                )
            elif not self._valid_base64(encoded):
                errors.append(f'{label}: base64_data повреждено')

        return TaskImportImageValidationResult(
            total=len(images),
            errors=tuple(errors),
            warnings=tuple(warnings),
        )

    @staticmethod
    def _uuid(value, *, label, field_name, errors):
        if not value:
            errors.append(f'{label}: отсутствует {field_name} (UUID)')
            return ''
        try:
            return normalize_task_import_uuid(value)
        except ValueError:
            errors.append(
                f'{label}: некорректный {field_name} UUID "{value}"',
            )
            return ''

    @staticmethod
    def _valid_base64(value):
        if not isinstance(value, str):
            return False
        encoded = value.split(',', 1)[1] if ',' in value else value
        try:
            base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError):
            return False
        return True
