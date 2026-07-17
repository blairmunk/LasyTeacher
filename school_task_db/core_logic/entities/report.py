"""Report DTOs."""

from dataclasses import dataclass
from typing import Any, List


@dataclass(frozen=True)
class EventsStatusReportData:
    events_by_status: List[dict]
    overdue_events: Any
    long_reviewing: Any
    completed_unchecked: Any
    participation_stats: List[dict]
    all_events: Any
    courses: Any
    active_report: str = 'events-status'
    active_course_pk: Any = None
