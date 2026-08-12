"""Command persistence boundary for event report narratives."""

from abc import ABC, abstractmethod

from core_logic.entities.event_performance_report import (
    SaveEventReportNarrativeParams,
    SaveEventReportNarrativeResult,
)


class IEventReportNarrativeCommandRepository(ABC):
    @abstractmethod
    def save_event_report_narrative(
        self,
        params: SaveEventReportNarrativeParams,
    ) -> SaveEventReportNarrativeResult:
        """Persist teacher-authored narrative sections."""
