"""Build event list page data."""

from core_logic.entities.event import EventListData
from core_logic.interfaces.event_repo import IEventRepository
from core_logic.services.event_service import EventService


class GetEventListUseCase:
    def __init__(
        self,
        event_repo: IEventRepository,
        event_service: EventService,
    ):
        self.event_repo = event_repo
        self.event_service = event_service

    def execute(self) -> EventListData:
        return self.event_service.build_list_data(
            self.event_repo.get_list_events(),
        )
