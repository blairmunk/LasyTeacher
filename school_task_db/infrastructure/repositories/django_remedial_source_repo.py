"""Django adapter for task exclusions used by remedial selection."""

from typing import Set

from core_logic.interfaces.remedial_source_repo import (
    IRemedialSourceRepository,
)
from events.models import EventParticipation
from works.models import VariantTask


class DjangoRemedialSourceRepository(IRemedialSourceRepository):
    def get_event_variant_task_ids(
        self,
        event_id: str,
        student_id: str,
    ) -> Set[str]:
        participation = EventParticipation.objects.filter(
            event_id=event_id,
            student_id=student_id,
        ).select_related('variant').first()
        if not participation or not participation.variant_id:
            return set()

        return {
            str(task_id)
            for task_id in VariantTask.objects.filter(
                variant_id=participation.variant_id,
            ).values_list('task_id', flat=True)
        }
