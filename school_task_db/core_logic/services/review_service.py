"""Pure helpers for the participation review screen."""

from dataclasses import dataclass
from typing import List, Optional

from core_logic.entities.review import (
    ReviewParticipationRef,
    ReviewTaskScoreRow,
    ReviewVariantTaskRef,
)


@dataclass(frozen=True)
class ReviewNavigation:
    previous_participation: Optional[ReviewParticipationRef]
    next_participation: Optional[ReviewParticipationRef]
    current_position: int
    total_positions: int
    navigation_progress: float


class ReviewService:
    def build_task_score_rows(
        self,
        variant_tasks: List[ReviewVariantTaskRef],
        existing_scores: dict,
    ) -> List[ReviewTaskScoreRow]:
        rows = []
        for index, variant_task in enumerate(variant_tasks, start=1):
            task_id = str(variant_task.task.id)
            score_data = existing_scores.get(task_id, {})
            rows.append(
                ReviewTaskScoreRow(
                    task=variant_task.task,
                    number=index,
                    points=score_data.get('points', 0),
                    max_points=score_data.get('max_points', variant_task.weight),
                    comment=score_data.get('comment', ''),
                )
            )
        return rows

    def build_navigation(
        self,
        participations: List[ReviewParticipationRef],
        current_participation_id: str,
    ) -> ReviewNavigation:
        total = len(participations)
        try:
            current_index = next(
                index
                for index, participation in enumerate(participations)
                if str(participation.pk) == str(current_participation_id)
            )
        except StopIteration:
            current_index = 0

        return ReviewNavigation(
            previous_participation=(
                participations[current_index - 1]
                if current_index > 0 and total > 0
                else None
            ),
            next_participation=(
                participations[current_index + 1]
                if current_index < total - 1
                else None
            ),
            current_position=current_index + 1 if total > 0 else 0,
            total_positions=total,
            navigation_progress=(
                round((current_index + 1) / total * 100, 1)
                if total > 0
                else 0
            ),
        )
