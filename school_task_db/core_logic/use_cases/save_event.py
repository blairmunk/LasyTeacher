"""Create and update events."""

from dataclasses import dataclass

from core_logic.interfaces.event_repo import CreateEventParams, IEventRepository


@dataclass(frozen=True)
class SaveEventResult:
    status: str
    event_id: str = ''


class CreateEventUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(self, params: CreateEventParams) -> SaveEventResult:
        event_id = self.event_repo.create_event(params)
        return SaveEventResult(status='created', event_id=event_id)


class UpdateEventUseCase:
    def __init__(self, event_repo: IEventRepository):
        self.event_repo = event_repo

    def execute(self, params: CreateEventParams) -> SaveEventResult:
        updated = self.event_repo.update_event(params)
        if not updated:
            return SaveEventResult(status='not_found')

        return SaveEventResult(status='updated', event_id=params.event_id)
