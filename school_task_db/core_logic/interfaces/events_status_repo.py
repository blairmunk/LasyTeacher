"""Port for events status report data."""

from abc import ABC, abstractmethod

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.entities.report_summary import EventsStatusSource


class IEventsStatusRepository(ABC):
    @abstractmethod
    def get_events_status_source(
        self,
        year: AcademicYearRef | None,
    ) -> EventsStatusSource:
        """Return normalized facts for the events status report."""
