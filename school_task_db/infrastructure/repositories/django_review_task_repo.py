"""Django read adapter for variant task snapshots used by review."""

from typing import List

from core_logic.entities.review import (
    ReviewTaskRef,
    ReviewTopicRef,
    ReviewVariantTaskRef,
)
from core_logic.interfaces.review_task_repo import IReviewTaskRepository
from events.models import EventParticipation
from infrastructure.services.task_content_snapshots import (
    task_content_snapshot_from_mapping,
)
from works.models import VariantTask


class DjangoReviewTaskRepository(IReviewTaskRepository):
    def get_variant_tasks(
        self,
        participation_id: str,
    ) -> List[ReviewVariantTaskRef]:
        participation = EventParticipation.objects.select_related(
            'variant',
        ).get(pk=participation_id)
        if not participation.variant:
            return []

        variant_tasks = VariantTask.objects.filter(
            variant=participation.variant,
        ).order_by('order')

        result = []
        for variant_task in variant_tasks:
            task = task_content_snapshot_from_mapping(
                variant_task.task_snapshot,
            )
            result.append(ReviewVariantTaskRef(
                task=ReviewTaskRef(
                    id=task.task_id,
                    text=task.text,
                    answer=task.answer,
                    short_solution=task.short_solution,
                    difficulty=task.difficulty,
                    topic=(
                        ReviewTopicRef(
                            pk=task.topic_id,
                            name=task.topic_name,
                        )
                        if task.topic_id
                        else None
                    ),
                ),
                variant_task_id=str(variant_task.pk),
                weight=variant_task.max_points or variant_task.weight,
                is_assessable=variant_task.is_assessable,
            ))
        return result

