"""Analyze task image placement and apply suggested missing positions."""

from collections import Counter
from typing import Sequence

from core_logic.entities.task_image_audit import (
    TaskImageAuditData,
    TaskImagePositionCount,
    TaskImagePositionSuggestion,
)
from core_logic.interfaces.task_image_audit_repo import ITaskImageAuditRepository
from core_logic.value_objects.task_image_position import (
    suggest_task_image_position,
    task_image_position_label,
)


MISSING_POSITION = 'missing'
MISSING_POSITION_LABEL = 'Позиция не задана'


class AnalyzeTaskImagesUseCase:
    def __init__(self, image_repo: ITaskImageAuditRepository):
        self.image_repo = image_repo

    def execute(self) -> TaskImageAuditData:
        images = tuple(self.image_repo.list_task_images())
        total = len(images)
        counts = Counter(image.position or MISSING_POSITION for image in images)
        missing_images = tuple(image for image in images if not image.position)

        distribution = tuple(
            TaskImagePositionCount(
                position=position,
                label=(
                    MISSING_POSITION_LABEL
                    if position == MISSING_POSITION
                    else task_image_position_label(position)
                ),
                count=count,
                percentage=(count / total * 100) if total else 0,
            )
            for position, count in sorted(counts.items())
        )
        suggestions = tuple(
            self._suggest(image.pk, image.caption)
            for image in missing_images
        )
        return TaskImageAuditData(
            total_images=total,
            distribution=distribution,
            missing_images=missing_images,
            suggestions=suggestions,
        )

    @staticmethod
    def _suggest(image_id: str, caption: str) -> TaskImagePositionSuggestion:
        position = suggest_task_image_position(caption)
        return TaskImagePositionSuggestion(
            image_id=image_id,
            position=position,
            position_label=task_image_position_label(position),
        )


class ApplyTaskImagePositionSuggestionsUseCase:
    def __init__(self, image_repo: ITaskImageAuditRepository):
        self.image_repo = image_repo

    def execute(
        self,
        suggestions: Sequence[TaskImagePositionSuggestion],
    ) -> int:
        return self.image_repo.apply_position_suggestions(suggestions)
