"""Django persistence for immutable checked-attempt revisions."""

from decimal import Decimal, InvalidOperation

from django.db.models import Max

from core_logic.entities.attempt_snapshot import AttemptSnapshotRef
from core_logic.interfaces.attempt_snapshot_repo import (
    IAttemptSnapshotRepository,
)
from core_logic.value_objects.task_scores import resolve_task_score_record
from events.models import AttemptSnapshot, AttemptTaskSnapshot, Mark
from infrastructure.services.task_content_snapshots import (
    task_content_snapshot_from_mapping,
)
from works.models import VariantTask


class DjangoAttemptSnapshotRepository(IAttemptSnapshotRepository):
    def capture_mark(self, mark_id: str) -> AttemptSnapshotRef:
        mark = Mark.objects.select_related(
            'participation__student',
            'participation__event__work',
            'participation__variant',
        ).get(pk=mark_id)
        participation = mark.participation
        event = participation.event
        variant = participation.variant
        latest_revision = AttemptSnapshot.objects.filter(
            participation=participation,
        ).aggregate(value=Max('revision'))['value'] or 0
        snapshot = AttemptSnapshot.objects.create(
            participation=participation,
            mark=mark,
            revision=latest_revision + 1,
            student_id_snapshot=str(participation.student_id),
            student_name_snapshot=participation.student.get_full_name(),
            event_id_snapshot=str(event.pk),
            event_name_snapshot=event.name,
            event_date_snapshot=event.planned_date,
            work_id_snapshot=str(event.work_id),
            work_name_snapshot=(
                variant.work_name_snapshot
                if variant and variant.work_name_snapshot
                else event.work.name
            ),
            variant_id_snapshot=str(participation.variant_id or ''),
            variant_number_snapshot=variant.number if variant else None,
            score=mark.score,
            points=self._decimal(mark.points),
            max_points=self._decimal(mark.max_points),
            teacher_comment=mark.teacher_comment,
            mistakes_analysis=mark.mistakes_analysis,
            recommendations=mark.recommendations,
            checked_at_snapshot=mark.checked_at,
            checked_by_snapshot=mark.checked_by,
            is_retake=mark.is_retake,
            is_excellent=mark.is_excellent,
            needs_attention=mark.needs_attention,
            task_scores_snapshot=dict(mark.task_scores or {}),
        )
        self._capture_task_results(snapshot, variant, mark.task_scores)
        return AttemptSnapshotRef(
            pk=str(snapshot.pk),
            participation_id=str(participation.pk),
            mark_id=str(mark.pk),
            revision=snapshot.revision,
        )

    def _capture_task_results(self, snapshot, variant, task_scores):
        if variant is None:
            return
        rows = []
        for variant_task in VariantTask.objects.filter(
            variant=variant,
        ).order_by('order', 'pk'):
            task = task_content_snapshot_from_mapping(
                variant_task.task_snapshot,
            )
            record = resolve_task_score_record(
                task_scores,
                variant_task_id=str(variant_task.pk),
                task_id=task.task_id,
            )
            rows.append(AttemptTaskSnapshot(
                attempt=snapshot,
                variant_task=variant_task,
                task_id_snapshot=task.task_id,
                order_snapshot=variant_task.order,
                is_assessable_snapshot=variant_task.is_assessable,
                expected_max_points_snapshot=variant_task.max_points,
                points=self._decimal(record.points) if record else None,
                checked_max_points=(
                    self._decimal(record.max_points) if record else None
                ),
                comment=record.comment if record else '',
            ))
        AttemptTaskSnapshot.objects.bulk_create(rows)

    @staticmethod
    def _decimal(value):
        if value in (None, ''):
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return None

