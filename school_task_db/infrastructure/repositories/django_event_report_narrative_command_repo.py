"""Django command adapter for teacher-authored event report narratives."""

from core_logic.entities.event_performance_report import (
    SaveEventReportNarrativeParams,
    SaveEventReportNarrativeResult,
)
from core_logic.interfaces.event_report_narrative_command_repo import (
    IEventReportNarrativeCommandRepository,
)
from events.models import Event
from reports.models import EventReportNarrativeModel


class DjangoEventReportNarrativeCommandRepository(
    IEventReportNarrativeCommandRepository,
):
    def save_event_report_narrative(
        self,
        params: SaveEventReportNarrativeParams,
    ) -> SaveEventReportNarrativeResult:
        if not Event.objects.filter(pk=params.event_id).exists():
            return SaveEventReportNarrativeResult(status='not_found')
        narrative = params.narrative
        EventReportNarrativeModel.objects.update_or_create(
            event_id=params.event_id,
            defaults={
                'possible_causes': narrative.possible_causes,
                'recommendations': narrative.recommendations,
                'planned_actions': narrative.planned_actions,
                'additional_notes': narrative.additional_notes,
            },
        )
        return SaveEventReportNarrativeResult(
            status='saved',
            event_id=params.event_id,
        )
