"""Django task image import component."""

import base64
from typing import Any, Dict, Optional
from uuid import UUID

from django.core.files.base import ContentFile

from tasks.models import Task, TaskImage


class TaskImageImporter:
    def __init__(self, runtime, context):
        self.runtime = runtime
        self.context = context

    def import_images(self, images_data):
        self.runtime._write('🖼️ Импорт изображений заданий...')
        for image_data in images_data:
            try:
                self._import_image(image_data)
            except Exception as error:
                self.runtime.log_error(
                    f'Ошибка импорта изображения: {error}',
                    error,
                )

    def _import_image(self, image_data: Dict[str, Any]):
        task_uuid = image_data.get('task_uuid') or image_data.get('task_id')
        if task_uuid not in self.context.imported_tasks:
            suffix = task_uuid[-8:] if task_uuid else 'Unknown'
            self.runtime.log_warning(
                f'Задание не найдено для изображения: {suffix}',
            )
            return

        task = self.context.imported_tasks[task_uuid]
        image_uuid = self.runtime.generate_uuid_if_missing(image_data, 'id')
        existing_image = self.runtime.safe_get_by_uuid(TaskImage, image_uuid)
        if existing_image and not self.runtime.should_create_object(
            existing_image,
            image_data,
            'images',
        ):
            if self.runtime.mode == 'update':
                if self._update_image(existing_image, image_data):
                    self.runtime.stats.record_updated(
                        'images',
                        existing_image.pk,
                    )
            return

        if not existing_image:
            image = self._create_image(task, image_uuid, image_data)
            if image:
                self.runtime.stats.record_created('images', image.pk)
                self.runtime.log_success(
                    'Создано изображение для задания '
                    f'{task.get_short_uuid()}',
                )

    def _create_image(
        self,
        task: Task,
        image_uuid: str,
        image_data: Dict[str, Any],
    ) -> Optional[TaskImage]:
        try:
            UUID(image_uuid)
        except ValueError as error:
            self.runtime.log_error(
                f'Некорректный UUID изображения: {image_uuid} - {error}',
            )
            return None

        image_content = self._decode_content(image_data)
        if image_content is None:
            return None

        try:
            position = image_data.get('position', '')
            task_image = TaskImage.objects.create(
                id=image_uuid,
                task=task,
                image=image_content,
                position=position,
                caption=image_data.get('caption', ''),
                order=image_data.get('order', 1),
            )
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка создания изображения: {error}',
                error,
                context={'image_id': image_uuid, 'task_id': str(task.pk)},
            )
            return None

        if position:
            self.runtime.log_info(
                f'Изображение создано с позицией: {position}',
            )
        else:
            self.runtime.log_info('Изображение создано без позиции')
            self.runtime.stats.add_warning(
                f'Изображение {image_uuid[-8:]} создано без позиции',
            )
        return task_image

    def _update_image(self, image: TaskImage, image_data: Dict[str, Any]):
        try:
            image.position = image_data.get('position', image.position)
            image.caption = image_data.get('caption', image.caption)
            image.order = image_data.get('order', image.order)
            if 'base64_data' in image_data:
                image_content = self._decode_content(
                    image_data,
                    default_filename=f'updated_{image.image.name}',
                )
                if image_content is None:
                    return False
                image.image = image_content
            image.save()
            self.runtime.log_success(
                f'Обновлено изображение {image.get_short_uuid()}',
            )
            return True
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка обновления изображения: {error}',
                error,
            )
            return False

    def _decode_content(
        self,
        image_data: Dict[str, Any],
        default_filename: str = 'imported_image.jpg',
    ):
        encoded = image_data.get('base64_data')
        if not encoded:
            self.runtime.log_warning(
                'Нет данных изображения (поле base64_data)',
            )
            return None
        if ',' in encoded:
            encoded = encoded.split(',', 1)[1]
        filename = image_data.get('filename', default_filename)
        try:
            return ContentFile(
                base64.b64decode(encoded, validate=True),
                name=filename,
            )
        except Exception as error:
            self.runtime.log_error(
                f'Ошибка декодирования base64: {error}',
                error,
            )
            return None
