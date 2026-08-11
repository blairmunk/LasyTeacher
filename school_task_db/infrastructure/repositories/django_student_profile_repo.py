"""Django repository for student profile learning history."""

from typing import List

from core_logic.entities.student import (
    EventRef,
    MarkRef,
    ObjectRef,
    StudentParticipationProfile,
    StudentTaskResultProfile,
    WorkGroupRef,
    WorkRef,
)
from core_logic.interfaces.student_profile_repo import IStudentProfileRepository
from core_logic.value_objects.attempt_status import (
    resolve_historical_participation_status,
)
from events.models import EventParticipation
from infrastructure.repositories.django_student_learning_support import (
    first_analog_groups,
    latest_task_history,
    result_is_correct,
    result_percentage,
)
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from works.models import WorkAnalogGroup


class DjangoStudentProfileRepository(IStudentProfileRepository):
    def get_profile_participations(
        self,
        student_id: str,
    ) -> List[StudentParticipationProfile]:
        participations = list(
            EventParticipation.objects.filter(
                student_id=student_id,
            ).select_related(
                'event',
                'event__work',
                'variant',
            ).order_by('-event__planned_date')
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in participations),
            include_task_results=False,
        )

        rows = []
        for participation in participations:
            event = participation.event
            work = event.work if event else None
            attempt = attempts.get(participation.pk)
            event_name = attempt.event_name_snapshot if attempt else event.name
            event_date = (
                attempt.event_date_snapshot if attempt else event.planned_date
            )
            rows.append(
                StudentParticipationProfile(
                    participation=ObjectRef(
                        pk=str(participation.pk),
                        name=str(participation),
                    ),
                    event=EventRef(
                        pk=str(event.pk),
                        name=event_name,
                        planned_date=event_date,
                    ),
                    work=(
                        WorkRef(
                            pk=str(work.pk),
                            name=(
                                attempt.work_name_snapshot
                                if attempt
                                else work.name
                            ),
                            work_type=work.work_type,
                            work_type_display=work.get_work_type_display(),
                        )
                        if work
                        else None
                    ),
                    mark=(
                        MarkRef(
                            pk=str(attempt.mark_id),
                            score=attempt.score,
                            points=attempt.points,
                            max_points=attempt.max_points,
                            teacher_comment=attempt.teacher_comment,
                        )
                        if attempt
                        else None
                    ),
                    score=attempt.score if attempt else None,
                    is_absent=(
                        resolve_historical_participation_status(
                            participation.status,
                            has_attempt=attempt is not None,
                        ) == 'absent'
                    ),
                    variant_number=(
                        attempt.variant_number_snapshot
                        if attempt
                        else (
                            participation.variant.number
                            if participation.variant
                            else None
                        )
                    ),
                )
            )
        return rows

    def get_task_logs(self, student_id: str) -> List[StudentTaskResultProfile]:
        results = latest_task_history([student_id])
        analog_groups = first_analog_groups(
            result.task.task_id for result in results
        )
        return [
            StudentTaskResultProfile(
                task=ObjectRef(pk=result.task.task_id, name=result.task.text),
                event=ObjectRef(pk=result.event_id, name=result.event_name),
                topic_name=result.task.topic_name,
                analog_group=(
                    ObjectRef(
                        pk=str(analog_groups[result.task.task_id].pk),
                        name=analog_groups[result.task.task_id].name,
                    )
                    if result.task.task_id in analog_groups
                    else None
                ),
                difficulty=result.task.difficulty,
                points=result.points,
                max_points=result.max_points,
                is_correct=result_is_correct(result),
                percentage=result_percentage(result),
                completed_at=result.captured_at,
            )
            for result in sorted(
                results,
                key=lambda item: item.captured_at,
                reverse=True,
            )
        ]

    def get_work_group_refs(self, work_ids: List[str]) -> List[WorkGroupRef]:
        if not work_ids:
            return []
        return [
            WorkGroupRef(
                work_id=str(work_group.work_id),
                group_id=str(work_group.analog_group_id),
                group_name=work_group.analog_group.name,
            )
            for work_group in WorkAnalogGroup.objects.filter(
                work_id__in=work_ids,
            ).select_related('analog_group')
        ]
