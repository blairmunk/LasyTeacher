"""Django adapter for task image position diagnostics."""

from django.db import transaction

from core_logic.entities.task_image_audit import TaskImageAuditSource
from core_logic.interfaces.task_image_audit_command_repo import (
    ITaskImageAuditCommandRepository,
)
from core_logic.interfaces.task_image_audit_query_repo import (
    ITaskImageAuditQueryRepository,
)
from tasks.models import TaskImage


class DjangoTaskImageAuditRepository(
    ITaskImageAuditQueryRepository,
    ITaskImageAuditCommandRepository,
):
    def list_task_images(self):
        return [
            TaskImageAuditSource(
                pk=str(image.pk),
                task_text=image.task.text,
                topic_name=(image.task.topic.name if image.task.topic else ''),
                filename=image.image.name,
                caption=image.caption or '',
                position=image.position or '',
            )
            for image in TaskImage.objects.select_related('task__topic')
        ]

    @transaction.atomic
    def apply_position_suggestions(self, suggestions):
        suggestions_by_id = {
            suggestion.image_id: suggestion.position
            for suggestion in suggestions
        }
        images = list(
            TaskImage.objects.filter(
                pk__in=suggestions_by_id,
                position='',
            ),
        )
        for image in images:
            image.position = suggestions_by_id[str(image.pk)]
        if images:
            TaskImage.objects.bulk_update(images, ['position'])
        return len(images)
