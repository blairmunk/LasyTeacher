"""Django read adapter for task image position diagnostics."""

from core_logic.entities.task_image_audit import TaskImageAuditSource
from core_logic.interfaces.task_image_audit_query_repo import (
    ITaskImageAuditQueryRepository,
)
from tasks.models import TaskImage


class DjangoTaskImageAuditQueryRepository(ITaskImageAuditQueryRepository):
    def list_task_images(self):
        return [
            TaskImageAuditSource(
                pk=str(image.pk),
                task_text=image.task.text,
                topic_name=(image.task.topic.name if image.task.topic else ''),
                filename=(
                    image.asset.file.name
                    if image.asset_id and image.asset.file
                    else ''
                ),
                caption=image.caption or '',
                position=image.position or '',
            )
            for image in TaskImage.objects.select_related(
                'asset',
                'task__topic',
            )
        ]
