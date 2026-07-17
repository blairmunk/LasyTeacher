"""Build a lightweight event participation reference."""

from dataclasses import dataclass
from typing import Optional

from core_logic.entities.event import EventParticipationRef
from core_logic.interfaces.event_repo import IEventRepository


@dataclass(frozen=True)
class EventParticipationRefData:
    participation: Optional[EventParticipationRef]
    status: str = 'ready'


class GetEventParticipationRefUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(self, participation_id: str) -> EventParticipationRefData:
        participation = self.event_repo.get_participation_ref(
            str(participation_id),
        )
        if not participation:
            return EventParticipationRefData(
                participation=None,
                status='not_found',
            )
        return EventParticipationRefData(participation=participation)
