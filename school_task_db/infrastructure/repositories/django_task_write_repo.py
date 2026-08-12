"""Django repository for task write operations."""

from typing import List

from core_logic.entities.task import (
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskSaveParams,
    TaskSaveResult,
)
from core_logic.interfaces.task_command_repo import ITaskCommandRepository
from core_logic.interfaces.task_image_command_repo import (
    ITaskImageCommandRepository,
)
from core_logic.interfaces.task_lifecycle_command_repo import (
    ITaskLifecycleCommandRepository,
)
from tasks.models import Task, TaskImage


class DjangoTaskWriteRepository(
    ITaskCommandRepository,
    ITaskImageCommandRepository,
    ITaskLifecycleCommandRepository,
):
    def create_task(self, params: TaskSaveParams) -> TaskSaveResult:
        task = Task.objects.create(**self._task_values(params))
        return TaskSaveResult(status='created', task_id=str(task.pk))

    def update_task(self, params: TaskSaveParams) -> TaskSaveResult:
        task = Task.objects.filter(pk=params.task_id).first()
        if task is None:
            return TaskSaveResult(status='not_found')

        for field, value in self._task_values(params).items():
            setattr(task, field, value)
        task.save()
        return TaskSaveResult(status='updated', task_id=str(task.pk))

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

    @staticmethod
    def _task_values(params: TaskSaveParams):
        return {
            'text': params.text,
            'answer': params.answer,
            'topic_id': params.topic_id,
            'subtopic_id': params.subtopic_id,
            'task_type': params.task_type,
            'difficulty': params.difficulty,
            'cognitive_level': params.cognitive_level,
            'content_element': params.content_element,
            'requirement_element': params.requirement_element,
            'short_solution': params.short_solution,
            'full_solution': params.full_solution,
            'hint': params.hint,
            'instruction': params.instruction,
            'estimated_time': params.estimated_time,
            'source_id': params.source_id,
            'source_detail': params.source_detail,
            'grade': params.grade,
            'year': params.year,
            'is_verified': params.is_verified,
            'teacher_notes': params.teacher_notes,
        }

    def delete_task(self, task_id: str) -> int:
        tasks = Task.objects.filter(pk=task_id)
        deleted_count = tasks.count()
        tasks.delete()
        return deleted_count
