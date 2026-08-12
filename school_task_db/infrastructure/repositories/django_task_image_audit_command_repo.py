"""Django command adapter for task image position diagnostics."""

from django.db import transaction

from core_logic.interfaces.task_image_audit_command_repo import (
    ITaskImageAuditCommandRepository,
)
from tasks.models import TaskImage


class DjangoTaskImageAuditCommandRepository(
    ITaskImageAuditCommandRepository,
):
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
