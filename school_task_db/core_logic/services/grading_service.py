"""Pure grading decisions."""

from collections.abc import Mapping

from core_logic.entities.review import NormalizedReviewTaskScores


class GradingService:
    """Business rules for grading workflow state."""

    def checked_by_name(self, display_name: str = '', username: str = '') -> str:
        return display_name or username or 'Учитель'

    def next_event_status(
        self,
        current_status: str,
        active_participants: int,
        graded_participants: int,
    ) -> str:
        if active_participants > 0 and active_participants == graded_participants:
            return 'graded'
        if current_status not in ('reviewing', 'graded'):
            return 'reviewing'
        return current_status

    def normalize_task_scores(self, variant_tasks, submitted_scores):
        submitted_scores = (
            submitted_scores
            if isinstance(submitted_scores, Mapping)
            else {}
        )
        score_rows = [
            (str(key), value)
            for key, value in submitted_scores.items()
            if isinstance(value, Mapping)
        ]
        normalized = {}
        points_total = 0
        max_points_total = 0
        for variant_task in variant_tasks:
            if not variant_task.is_assessable:
                continue
            task_id = str(variant_task.task.id)
            variant_task_id = str(variant_task.variant_task_id or '')
            submitted = self._submitted_task_score(
                score_rows,
                variant_task_id=variant_task_id,
                task_id=task_id,
            )
            max_points = max(self._int_or_default(variant_task.weight, 0), 0)
            points = min(
                max(self._int_or_default(submitted.get('points'), 0), 0),
                max_points,
            )
            score_key = variant_task_id or task_id
            normalized_score = {
                'task_id': task_id,
                'points': points,
                'max_points': max_points,
                'comment': str(submitted.get('comment') or ''),
            }
            if variant_task_id:
                normalized_score['variant_task_id'] = variant_task_id
            normalized[score_key] = normalized_score
            points_total += points
            max_points_total += max_points

        return NormalizedReviewTaskScores(
            task_scores=normalized,
            points=points_total,
            max_points=max_points_total,
        )

    @staticmethod
    def _submitted_task_score(score_rows, variant_task_id, task_id):
        for score_key, score in score_rows:
            submitted_variant_task_id = str(
                score.get('variant_task_id') or ''
            )
            if variant_task_id and (
                score_key == variant_task_id
                or submitted_variant_task_id == variant_task_id
            ):
                return score
        for score_key, score in score_rows:
            submitted_task_id = str(score.get('task_id') or '')
            if score_key == task_id or submitted_task_id == task_id:
                return score
        return {}

    @staticmethod
    def _int_or_default(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
