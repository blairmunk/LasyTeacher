"""Change an event status when the transition is allowed."""

from dataclasses import dataclass

from core_logic.interfaces.event_repo import IEventRepository
from core_logic.services.event_service import EventService


@dataclass(frozen=True)
class ChangeEventStatusRequest:
    event_id: str
    new_status: str


@dataclass(frozen=True)
class ChangeEventStatusResult:
    success: bool
    current_status: str
    new_status: str
    new_status_label: str = ''


class ChangeEventStatusUseCase:
    def __init__(
        self,
        event_repo: IEventRepository,
        event_service: EventService,
    ):
        self.event_repo = event_repo
        self.event_service = event_service

    def execute(self, request: ChangeEventStatusRequest) -> ChangeEventStatusResult:
        current_status = self.event_repo.get_event_status(request.event_id)
        if not current_status:
            return ChangeEventStatusResult(
                success=False,
                current_status='',
                new_status=request.new_status,
            )

        if not self.event_service.can_change_status(
            current_status=current_status,
            new_status=request.new_status,
        ):
            return ChangeEventStatusResult(
                success=False,
                current_status=current_status,
                new_status=request.new_status,
            )

        self.event_repo.set_event_status(
            event_id=request.event_id,
            status=request.new_status,
        )
        return ChangeEventStatusResult(
            success=True,
            current_status=current_status,
            new_status=request.new_status,
            new_status_label=self.event_service.status_label(request.new_status),
        )
