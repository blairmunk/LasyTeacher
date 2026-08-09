"""Django persistence for immutable checked-attempt revisions."""

from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.db.models import Max

from core_logic.entities.attempt_snapshot import AttemptSnapshotRef
from core_logic.interfaces.attempt_snapshot_repo import (
    IAttemptSnapshotRepository,
)
from core_logic.value_objects.task_scores import (
    resolve_task_score_record,
    task_score_records_for_attempt,
)
from core_logic.value_objects.task_content_snapshot import (
    task_content_snapshot_from_mapping,
)
from events.models import AttemptSnapshot, AttemptTaskSnapshot, Mark
from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
from task_groups.models import TaskGroup
from tasks.models import Task
from works.models import VariantTask, WorkAnalogGroup


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
            work_assessment_mode_snapshot=event.work.assessment_mode,
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
            self._capture_unassigned_task_results(snapshot, task_scores)
            return
        variant_tasks = list(
            VariantTask.objects.filter(
                variant=variant,
            ).order_by('order', 'pk')
        )
        selection_names = self._selection_names_by_variant_task(variant_tasks)
        rows = []
        for variant_task in variant_tasks:
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
                task_content_snapshot=dict(variant_task.task_snapshot),
                source_selection_id_snapshot=(
                    variant_task.source_selection_id
                ),
                source_selection_name_snapshot=selection_names.get(
                    str(variant_task.pk),
                    '',
                ),
                content_order_snapshot=variant_task.content_order,
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

    @classmethod
    def _selection_names_by_variant_task(cls, variant_tasks):
        selection_id_by_variant_task = {
            str(variant_task.pk): cls._valid_uuid(
                variant_task.source_selection_id,
            )
            for variant_task in variant_tasks
        }
        selection_ids = {
            selection_id
            for selection_id in selection_id_by_variant_task.values()
            if selection_id
        }
        names_by_selection_id = {}
        if selection_ids:
            names_by_selection_id = {
                str(selection_id): group_name
                for selection_id, group_name in WorkAnalogGroup.objects.filter(
                    pk__in=selection_ids,
                ).values_list('pk', 'analog_group__name')
            }

        result = {}
        unresolved = []
        for variant_task in variant_tasks:
            variant_task_id = str(variant_task.pk)
            group_name = names_by_selection_id.get(
                selection_id_by_variant_task[variant_task_id],
                '',
            )
            if group_name:
                result[variant_task_id] = group_name
            else:
                unresolved.append(variant_task)

        if not unresolved:
            return result

        fallback_names_by_task_id = {}
        fallback_rows = TaskGroup.objects.filter(
            task_id__in={variant_task.task_id for variant_task in unresolved},
        ).order_by('task_id', 'pk').values_list('task_id', 'group__name')
        for task_id, group_name in fallback_rows:
            fallback_names_by_task_id.setdefault(str(task_id), group_name)
        for variant_task in unresolved:
            group_name = fallback_names_by_task_id.get(
                str(variant_task.task_id),
                '',
            )
            if group_name:
                result[str(variant_task.pk)] = group_name
        return result

    @staticmethod
    def _valid_uuid(value):
        if not value:
            return ''
        try:
            return str(UUID(str(value)))
        except (AttributeError, TypeError, ValueError):
            return ''

    def _capture_unassigned_task_results(self, snapshot, task_scores):
        records = task_score_records_for_attempt(task_scores)
        snapshots = build_task_content_snapshots(
            Task.objects.filter(
                pk__in=[record.task_id for record in records],
            )
        )
        rows = []
        for order, record in enumerate(records, start=1):
            task_snapshot = snapshots.get(record.task_id)
            if task_snapshot is None:
                continue
            checked_max_points = self._decimal(record.max_points)
            rows.append(AttemptTaskSnapshot(
                attempt=snapshot,
                variant_task=None,
                task_id_snapshot=record.task_id,
                task_content_snapshot=task_snapshot.to_mapping(),
                order_snapshot=order,
                is_assessable_snapshot=True,
                expected_max_points_snapshot=checked_max_points or Decimal('0'),
                points=self._decimal(record.points),
                checked_max_points=checked_max_points,
                comment=record.comment,
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
