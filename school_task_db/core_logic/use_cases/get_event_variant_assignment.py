"""Build variant-assignment form data for an event."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.event import EventEntity, EventParticipationRow, EventVariantRef
from core_logic.interfaces.event_read_repo import IEventReadRepository


@dataclass(frozen=True)
class EventVariantAssignmentData:
    event: Optional[EventEntity]
    participations: tuple[EventParticipationRow, ...]
    variants: tuple[EventVariantRef, ...]
    status: str = 'ready'

    def __post_init__(self):
        object.__setattr__(self, 'participations', tuple(self.participations))
        object.__setattr__(self, 'variants', tuple(self.variants))


class GetEventVariantAssignmentUseCase:
    def __init__(self, event_repo: IEventReadRepository):
        self.event_repo = event_repo

    def execute(self, event_id: str) -> EventVariantAssignmentData:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            return EventVariantAssignmentData(
                event=None,
                participations=(),
                variants=(),
                status='not_found',
            )
        if not event.requires_variants:
            return EventVariantAssignmentData(
                event=event,
                participations=(),
                variants=(),
                status='variants_not_required',
            )
        return EventVariantAssignmentData(
            event=event,
            participations=self.event_repo.get_detail_participations(event_id),
            variants=self.event_repo.get_available_variants(event_id),
        )
