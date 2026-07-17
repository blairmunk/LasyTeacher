"""Build event detail page data."""

from core_logic.entities.event import EventDetailData
from core_logic.interfaces.event_repo import IEventRepository
from core_logic.services.event_service import EventService


class GetEventDetailUseCase:
    def __init__(
        self,
        event_repo: IEventRepository,
        event_service: EventService,
    ):
        self.event_repo = event_repo
        self.event_service = event_service

    def execute(self, event_id: str) -> EventDetailData:
        event = self.event_repo.get_by_id(event_id)
        if event is None:
            return EventDetailData()

        return self.event_service.build_detail_data(
            event=event,
            status=event.status,
            has_work=event.work_id is not None,
            participations=self.event_repo.get_detail_participations(event_id),
            available_variants=self.event_repo.get_available_variants(event_id),
        )
