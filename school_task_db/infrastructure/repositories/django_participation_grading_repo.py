"""Django write adapter for participation grading."""

from django.db import transaction
from django.utils import timezone

from core_logic.entities.event import ParticipationGradingContext
from core_logic.entities.grading import (
    GradeParticipationParams,
    GradeParticipationResult,
)
from core_logic.interfaces.participation_grading_repo import (
    IParticipationGradingRepository,
)
from events.models import Event, EventParticipation, Mark


class DjangoParticipationGradingRepository(
    IParticipationGradingRepository,
):
    def get_participation_grading_context(
        self,
        participation_id: str,
    ) -> ParticipationGradingContext:
        participation = EventParticipation.objects.select_for_update().get(
            pk=participation_id,
        )
        event = Event.objects.select_for_update().get(
            pk=participation.event_id,
        )
        other_active = EventParticipation.objects.filter(
            event_id=event.pk,
        ).exclude(
            pk=participation.pk,
        ).exclude(
            status='absent',
        )
        return ParticipationGradingContext(
            event_status=event.status,
            other_active_participants=other_active.count(),
            other_graded_participants=other_active.filter(
                status='graded',
            ).count(),
        )

    def save_participation_grade(
        self,
        params: GradeParticipationParams,
    ) -> GradeParticipationResult:
        with transaction.atomic():
            participation = (
                EventParticipation.objects.select_for_update().select_related(
                    'student',
                    'event',
                ).get(pk=params.participation_id)
            )
            mark, _ = Mark.objects.get_or_create(participation=participation)

            mark.score = params.score
            mark.points = params.points
            mark.max_points = params.max_points
            mark.teacher_comment = params.teacher_comment
            mark.mistakes_analysis = params.mistakes_analysis
            mark.recommendations = params.recommendations
            mark.checked_at = timezone.now()
            mark.checked_by = params.checked_by
            mark.is_retake = params.is_retake
            mark.is_excellent = params.is_excellent
            mark.needs_attention = params.needs_attention
            if params.task_scores is not None:
                mark.task_scores = {
                    score.score_key: {
                        'task_id': score.task_id or score.score_key,
                        'points': score.points,
                        'max_points': score.max_points,
                        'comment': score.comment,
                        **(
                            {'variant_task_id': score.variant_task_id}
                            if score.variant_task_id
                            else {}
                        ),
                    }
                    for score in params.task_scores
                }
            if params.work_scan is not None:
                if mark.work_scan:
                    mark.work_scan.delete(save=False)
                mark.work_scan = params.work_scan
            mark.save()

            participation.status = 'graded'
            participation.graded_at = timezone.now()
            participation.save()

            event = participation.event
            if params.event_status is not None:
                event.status = params.event_status
                event.save(update_fields=['status'])

            student = participation.student
            return GradeParticipationResult(
                mark_id=str(mark.pk),
                participation_id=str(participation.pk),
                event_id=str(event.pk),
                student_name=f'{student.last_name} {student.first_name}',
                score=mark.score,
                event_status=event.status,
            )
