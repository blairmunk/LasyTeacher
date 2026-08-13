"""Command data for creating and updating events."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass(frozen=True)
class CreateEventParams:
    name: str
    work_id: str
    date: Optional[date | datetime] = None
    course_id: Optional[str] = None
    status: str = 'planned'
    location: str = ''
    description: str = ''
    event_id: str = ''
