"""Build participant-selection page data for an event."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.event import EventEntity, EventParticipationRow
from core_logic.interfaces.event_read_repo import IEventReadRepository


@dataclass(frozen=True)
class EventParticipantSelectionData:
    event: Optional[EventEntity]
    current_participants: tuple[EventParticipationRow, ...]
    status: str = 'ready'

    def __post_init__(self):
        object.__setattr__(
            self,
            'current_participants',
            tuple(self.current_participants),
        )


class GetEventParticipantSelectionUseCase:
    def __init__(self, event_repo: IEventReadRepository):
        self.event_repo = event_repo

    def execute(self, event_id: str) -> EventParticipantSelectionData:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            return EventParticipantSelectionData(
                event=None,
                current_participants=(),
                status='not_found',
            )
        return EventParticipantSelectionData(
            event=event,
            current_participants=self.event_repo.get_detail_participations(event_id),
        )
