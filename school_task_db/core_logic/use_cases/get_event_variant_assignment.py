"""Build variant-assignment form data for an event."""

from dataclasses import dataclass
from typing import List, Optional

from core_logic.entities.event import EventEntity, EventParticipationRow, EventVariantRef
from core_logic.interfaces.event_repo import IEventRepository


@dataclass(frozen=True)
class EventVariantAssignmentData:
    event: Optional[EventEntity]
    participations: List[EventParticipationRow]
    variants: List[EventVariantRef]
    status: str = 'ready'


class GetEventVariantAssignmentUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(self, event_id: str) -> EventVariantAssignmentData:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            return EventVariantAssignmentData(
                event=None,
                participations=[],
                variants=[],
                status='not_found',
            )
        return EventVariantAssignmentData(
            event=event,
            participations=self.event_repo.get_detail_participations(event_id),
            variants=self.event_repo.get_available_variants(event_id),
        )
