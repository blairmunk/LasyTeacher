"""Add participants to an event."""

from dataclasses import dataclass
from typing import Iterable

from core_logic.interfaces.event_repo import IEventRepository


@dataclass(frozen=True)
class AddEventParticipantsRequest:
    event_id: str
    student_ids: Iterable[str]


@dataclass(frozen=True)
class AddEventParticipantsResult:
    created_count: int


class AddEventParticipantsUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(
        self,
        request: AddEventParticipantsRequest,
    ) -> AddEventParticipantsResult:
        unique_student_ids = list(dict.fromkeys(
            str(student_id)
            for student_id in request.student_ids
            if student_id
        ))
        return AddEventParticipantsResult(
            created_count=self.event_repo.add_participants(
                event_id=request.event_id,
                student_ids=unique_student_ids,
            )
        )
