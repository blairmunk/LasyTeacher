"""Django command adapter for task images."""

from typing import List

from core_logic.entities.task import (
    TaskImageSaveParams,
    TaskImagesSaveResult,
)
from core_logic.interfaces.task_image_command_repo import (
    ITaskImageCommandRepository,
)
from tasks.models import Task, TaskImage


class DjangoTaskImageCommandRepository(ITaskImageCommandRepository):
    def save_task_images(
        self,
        task_id: str,
        images: List[TaskImageSaveParams],
    ) -> TaskImagesSaveResult:
        if not Task.objects.filter(pk=task_id).exists():
            return TaskImagesSaveResult(status='not_found')

        created_images = 0
        deleted_images = 0
        for image_params in images:
            if image_params.image_id:
                task_image = TaskImage.objects.filter(
                    pk=image_params.image_id,
                    task_id=task_id,
                ).first()
                if task_image is None:
                    continue
                if image_params.delete:
                    task_image.delete()
                    deleted_images += 1
                    continue

                if image_params.image:
                    task_image.image = image_params.image
                task_image.position = image_params.position
                task_image.caption = image_params.caption
                task_image.order = image_params.order
                task_image.save()
                continue

            if image_params.delete or not image_params.image:
                continue
            TaskImage.objects.create(
                task_id=task_id,
                image=image_params.image,
                position=image_params.position,
                caption=image_params.caption,
                order=image_params.order,
            )
            created_images += 1

        return TaskImagesSaveResult(
            status='saved',
            created_images=created_images,
            deleted_images=deleted_images,
        )
