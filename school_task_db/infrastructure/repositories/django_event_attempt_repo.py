"""Django repository for checked event attempts."""

from typing import Optional

from core_logic.entities.event import (
    CheckedAttemptRef,
    ParticipationAttemptData,
    StudentSummary,
    VariantSummary,
)
from core_logic.interfaces.event_attempt_repo import IEventAttemptRepository
from events.models import EventParticipation
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)


class DjangoEventAttemptRepository(IEventAttemptRepository):
    def get_latest_student_attempt(
        self,
        event_id: str,
        student_id: str,
    ) -> Optional[CheckedAttemptRef]:
        participation_id = EventParticipation.objects.filter(
            event_id=event_id,
            student_id=student_id,
        ).values_list(
            'pk',
            flat=True,
        ).first()
        if not participation_id:
            return None
        attempt = latest_attempts_by_participation(
            [participation_id],
            include_task_results=False,
        ).get(participation_id)
        if attempt is None:
            return None

        return CheckedAttemptRef(
            student_id=attempt.student_id_snapshot,
            event_id=attempt.event_id_snapshot,
            score=attempt.score,
            participation_id=str(attempt.participation_id),
            attempt_snapshot_id=str(attempt.pk),
        )

    def get_participation_attempts(self, event_id: str):
        participations = EventParticipation.objects.filter(
            event_id=event_id
        ).select_related('student', 'variant').order_by(
            'student__last_name',
            'student__first_name',
        )

        attempts = latest_attempts_by_participation(
            [participation.pk for participation in participations],
            include_task_results=False,
        )

        result = []
        for participation in participations:
            student = participation.student
            attempt = attempts.get(participation.pk)
            if attempt and attempt.variant_id_snapshot:
                variant = VariantSummary(
                    id=attempt.variant_id_snapshot,
                    number=attempt.variant_number_snapshot,
                )
            elif participation.variant:
                variant = VariantSummary(
                    id=str(participation.variant.pk),
                    number=participation.variant.number,
                )
            else:
                variant = None
            result.append(
                ParticipationAttemptData(
                    student=StudentSummary(
                        id=str(student.pk),
                        full_name=student.get_full_name(),
                        short_name=student.get_short_name(),
                    ),
                    variant=variant,
                    score=attempt.score if attempt else None,
                    points=attempt.points if attempt else None,
                    max_points=attempt.max_points if attempt else None,
                    task_scores=(
                        attempt.task_scores_snapshot if attempt else {}
                    ),
                )
            )
        return result
