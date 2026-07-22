"""Pure helpers for the participation review screen."""

from dataclasses import dataclass
from typing import Mapping, List, Optional

from core_logic.entities.review import (
    EventReviewData,
    EventReviewParticipationRow,
    ReviewDashboardData,
    ReviewEventProgress,
    ReviewFileValidationResult,
    ReviewParticipationRef,
    ReviewScoreCalculation,
    ReviewSubmissionData,
    ReviewVariantRef,
    ReviewTaskScoreRow,
    ReviewVariantTaskRef,
)
from core_logic.value_objects.task_scores import (
    task_score_records_by_score_key,
    task_score_records_by_task_id,
)


@dataclass(frozen=True)
class ReviewNavigation:
    previous_participation: Optional[ReviewParticipationRef]
    next_participation: Optional[ReviewParticipationRef]
    current_position: int
    total_positions: int
    navigation_progress: float


class ReviewService:
    MAX_WORK_SCAN_SIZE = 10 * 1024 * 1024
    ALLOWED_WORK_SCAN_TYPES = {
        'application/pdf',
        'image/jpeg',
        'image/png',
        'image/webp',
    }

    def calculate_score(self, points: int, max_points: int) -> ReviewScoreCalculation:
        percentage = (points / max_points) * 100 if max_points > 0 else 0

        if percentage >= 85:
            score = 5
        elif percentage >= 70:
            score = 4
        elif percentage >= 50:
            score = 3
        else:
            score = 2

        return ReviewScoreCalculation(
            score=score,
            percentage=round(percentage, 1),
        )

    def parse_submission(self, data: Mapping[str, object]) -> ReviewSubmissionData:
        task_scores = {}
        for key, value in data.items():
            if not key.startswith('task_'):
                continue
            if key.endswith(('_max', '_comment', '_task_id', '_variant_task_id')):
                continue

            score_key = key[5:]
            score_data = {
                'points': self._int_or_default(value, 0),
                'max_points': self._int_or_default(
                    data.get(f'task_{score_key}_max'),
                    5,
                ),
                'comment': data.get(f'task_{score_key}_comment', ''),
            }
            task_id = str(data.get(f'task_{score_key}_task_id') or '').strip()
            variant_task_id = str(
                data.get(f'task_{score_key}_variant_task_id') or ''
            ).strip()
            if task_id and task_id != score_key:
                score_data['task_id'] = task_id
            if variant_task_id:
                score_data['variant_task_id'] = variant_task_id

            task_scores[score_key] = score_data

        return ReviewSubmissionData(
            score=self._int_or_none(data.get('score')),
            points=self._int_or_none(data.get('points')),
            max_points=self._int_or_none(data.get('max_points')),
            teacher_comment=data.get('teacher_comment', ''),
            mistakes_analysis=data.get('mistakes_analysis', ''),
            recommendations=data.get('recommendations', ''),
            task_scores=task_scores,
        )

    def validate_work_scan(
        self,
        size: int,
        content_type: str,
    ) -> ReviewFileValidationResult:
        if size > self.MAX_WORK_SCAN_SIZE:
            return ReviewFileValidationResult(
                accepted=False,
                warning=(
                    f'⚠️ Файл слишком большой ({size // 1024 // 1024} МБ). '
                    'Максимум 10 МБ.'
                ),
            )
        if content_type not in self.ALLOWED_WORK_SCAN_TYPES:
            return ReviewFileValidationResult(
                accepted=False,
                warning=(
                    f'⚠️ Неподдерживаемый формат: {content_type}. '
                    'Допустимы: PDF, JPEG, PNG, WebP.'
                ),
            )

        return ReviewFileValidationResult(accepted=True)

    def build_dashboard(
        self,
        events: List[ReviewEventProgress],
    ) -> ReviewDashboardData:
        needs_review = []
        in_progress = []
        fully_graded = []

        for event_data in events:
            status = event_data.event.status
            if status in ('planned', 'in_progress'):
                needs_review.append(event_data)
            elif status == 'reviewing':
                in_progress.append(event_data)
            elif status == 'completed':
                if event_data.graded_participants == 0:
                    needs_review.append(event_data)
                else:
                    in_progress.append(event_data)
            elif status == 'graded':
                if event_data.progress_percentage >= 100:
                    fully_graded.append(event_data)
                else:
                    in_progress.append(event_data)
            else:
                if event_data.progress_percentage >= 100:
                    fully_graded.append(event_data)
                elif event_data.graded_participants > 0:
                    in_progress.append(event_data)
                else:
                    needs_review.append(event_data)

        return ReviewDashboardData(
            needs_review=needs_review,
            in_progress=in_progress,
            fully_graded=fully_graded,
            total_events=len(needs_review) + len(in_progress) + len(fully_graded),
        )

    def build_event_review(
        self,
        participations: List[EventReviewParticipationRow],
        available_variants: List[ReviewVariantRef],
        event=None,
    ) -> EventReviewData:
        total_participants = len(participations)
        has_participants = total_participants > 0
        variants_assigned = any(row.variant is not None for row in participations)
        all_variants_assigned = (
            has_participants
            and all(row.variant is not None for row in participations if not row.is_absent)
        )

        if not has_participants:
            return self._blocked_event_review(
                block_reason='no_participants',
                participations=participations,
                available_variants=available_variants,
                has_participants=False,
                variants_assigned=False,
                all_variants_assigned=False,
                event=event,
            )

        if not variants_assigned:
            return self._blocked_event_review(
                block_reason='no_variants',
                participations=participations,
                available_variants=available_variants,
                has_participants=True,
                variants_assigned=False,
                all_variants_assigned=False,
                event=event,
            )

        absent_count = sum(1 for row in participations if row.is_absent)
        scores = [
            row.mark.score
            for row in participations
            if row.has_mark and row.mark and row.mark.score is not None
        ]
        active_participants = total_participants - absent_count
        graded_count = len(scores)
        progress = (
            round(graded_count / active_participants * 100, 1)
            if active_participants > 0
            else 100
        )
        score_distribution = {2: 0, 3: 0, 4: 0, 5: 0}
        for score in scores:
            if score in score_distribution:
                score_distribution[score] += 1

        return EventReviewData(
            event=event,
            has_participants=has_participants,
            variants_assigned=variants_assigned,
            all_variants_assigned=all_variants_assigned,
            blocked=False,
            block_reason='',
            available_variants=available_variants,
            participations_data=participations,
            total_participants=total_participants,
            active_participants=active_participants,
            graded_participants=graded_count,
            absent_participants=absent_count,
            progress_percentage=progress,
            avg_score=round(sum(scores) / len(scores), 2) if scores else 0,
            score_distribution=score_distribution,
        )

    def build_task_score_rows(
        self,
        variant_tasks: List[ReviewVariantTaskRef],
        existing_scores: dict,
    ) -> List[ReviewTaskScoreRow]:
        rows = []
        for index, variant_task in enumerate(variant_tasks, start=1):
            task_id = str(variant_task.task.id)
            score_data = self._variant_task_score_data(
                existing_scores=existing_scores,
                variant_task=variant_task,
                task_id=task_id,
            )
            rows.append(
                ReviewTaskScoreRow(
                    task=variant_task.task,
                    number=index,
                    points=score_data.get('points', 0),
                    max_points=score_data.get('max_points', variant_task.weight),
                    variant_task_id=variant_task.variant_task_id,
                    comment=score_data.get('comment', ''),
                )
            )
        return rows

    def assessable_variant_tasks(
        self,
        variant_tasks: List[ReviewVariantTaskRef],
    ) -> List[ReviewVariantTaskRef]:
        return [
            variant_task
            for variant_task in variant_tasks
            if variant_task.is_assessable
        ]

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

    @staticmethod
    def _int_or_none(value) -> Optional[int]:
        if value in (None, ''):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _int_or_default(value, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _variant_task_score_data(
        existing_scores: dict,
        variant_task: ReviewVariantTaskRef,
        task_id: str,
    ) -> dict:
        records_by_score_key = task_score_records_by_score_key(existing_scores)
        if variant_task.variant_task_id:
            score_record = records_by_score_key.get(variant_task.variant_task_id)
            if score_record:
                return score_record.raw

        score_record = task_score_records_by_task_id(existing_scores).get(task_id)
        if score_record:
            return score_record.raw
        return {}

    def _blocked_event_review(
        self,
        block_reason: str,
        participations: List[EventReviewParticipationRow],
        available_variants: List[ReviewVariantRef],
        has_participants: bool,
        variants_assigned: bool,
        all_variants_assigned: bool,
        event=None,
    ) -> EventReviewData:
        return EventReviewData(
            event=event,
            has_participants=has_participants,
            variants_assigned=variants_assigned,
            all_variants_assigned=all_variants_assigned,
            blocked=True,
            block_reason=block_reason,
            available_variants=available_variants,
            participations_data=participations,
            total_participants=len(participations),
            active_participants=0,
            graded_participants=0,
            absent_participants=0,
            progress_percentage=0,
            avg_score=0,
            score_distribution={2: 0, 3: 0, 4: 0, 5: 0},
        )
