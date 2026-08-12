"""Read-only persistence boundary for event performance reports."""

from abc import ABC, abstractmethod

from core_logic.entities.event_performance_report import (
    EventPerformanceReportSource,
)


class IEventPerformanceReportQueryRepository(ABC):
    @abstractmethod
    def get_event_report_source(
        self,
        event_id: str,
    ) -> EventPerformanceReportSource | None:
        """Return normalized facts for one event report."""
