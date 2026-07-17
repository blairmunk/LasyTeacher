"""Build participant-selection page data for an event."""

from dataclasses import dataclass
from typing import List, Optional

from core_logic.entities.event import EventEntity, EventParticipationRow
from core_logic.interfaces.event_repo import IEventRepository


@dataclass(frozen=True)
class EventParticipantSelectionData:
    event: Optional[EventEntity]
    current_participants: List[EventParticipationRow]
    status: str = 'ready'


class GetEventParticipantSelectionUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(self, event_id: str) -> EventParticipantSelectionData:
        event = self.event_repo.get_by_id(event_id)
        if not event:
            return EventParticipantSelectionData(
                event=None,
                current_participants=[],
                status='not_found',
            )
        return EventParticipantSelectionData(
            event=event,
            current_participants=self.event_repo.get_detail_participations(event_id),
        )
