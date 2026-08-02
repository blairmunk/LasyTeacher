"""Persistence boundary for event performance reports."""

from abc import ABC, abstractmethod

from core_logic.entities.event_performance_report import (
    EventPerformanceReportSource,
    SaveEventReportNarrativeParams,
    SaveEventReportNarrativeResult,
)


class IEventPerformanceReportRepository(ABC):
    @abstractmethod
    def get_event_report_source(
        self,
        event_id: str,
    ) -> EventPerformanceReportSource | None:
        """Return normalized facts for one event report."""

    @abstractmethod
    def save_event_report_narrative(
        self,
        params: SaveEventReportNarrativeParams,
    ) -> SaveEventReportNarrativeResult:
        """Persist teacher-authored narrative sections."""
