"""Report repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from core_logic.entities.report import EventsStatusReportData, WorkAnalysisReportData


class IReportRepository(ABC):
    @abstractmethod
    def get_events_status_report(
        self,
        year: Any,
        current_date: datetime,
    ) -> EventsStatusReportData:
        """Return events status report data."""

    @abstractmethod
    def get_work_analysis_report(self, year: Any) -> WorkAnalysisReportData:
        """Return work analysis report data."""
