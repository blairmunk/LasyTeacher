"""Report repository interface."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from core_logic.entities.report import EventsStatusReportData


class IReportRepository(ABC):
    @abstractmethod
    def get_events_status_report(
        self,
        year: Any,
        current_date: datetime,
    ) -> EventsStatusReportData:
        """Return events status report data."""
