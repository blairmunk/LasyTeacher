"""Django repository for event participation commands."""

from typing import Mapping, Sequence

from django.db import transaction

from core_logic.entities.event import EventVariantAssignmentResult
from core_logic.interfaces.event_participation_repo import (
    IEventParticipationRepository,
)
from events.models import EventParticipation
from works.models import Variant


class DjangoEventParticipationRepository(IEventParticipationRepository):
    def add_participants(self, event_id: str, student_ids: Sequence[str]) -> int:
        created_count = 0
        with transaction.atomic():
            for student_id in student_ids:
                _, created = EventParticipation.objects.get_or_create(
                    event_id=event_id,
                    student_id=student_id,
                    defaults={'status': 'assigned'},
                )
                if created:
                    created_count += 1
        return created_count

    def assign_variants(
        self,
        event_id: str,
        assignments: Mapping[str, str],
    ) -> int:
        assigned_count = 0
        with transaction.atomic():
            participations = EventParticipation.objects.filter(
                event_id=event_id,
                pk__in=assignments.keys(),
            )
            for participation in participations:
                variant_id = assignments.get(str(participation.pk))
                if not variant_id:
                    continue
                participation.variant_id = variant_id
                participation.save()
                assigned_count += 1
        return assigned_count

    def assign_variant(
        self,
        event_id: str,
        participation_id: str,
        variant_id: str,
    ) -> EventVariantAssignmentResult:
        participation = EventParticipation.objects.select_related(
            'student',
        ).get(pk=participation_id, event_id=event_id)
        variant = Variant.objects.get(pk=variant_id)

        participation.variant = variant
        participation.save()
        return EventVariantAssignmentResult(
            variant_number=variant.number,
            student_last_name=participation.student.last_name,
            student_first_name=participation.student.first_name,
        )

    def create_participation(
        self,
        event_id: str,
        student_id: str,
        variant_id: str,
    ) -> str:
        participation = EventParticipation.objects.create(
            event_id=event_id,
            student_id=student_id,
            variant_id=variant_id,
            status='assigned',
        )
        return str(participation.pk)
