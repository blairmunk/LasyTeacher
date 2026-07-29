"""Academic year read models."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AcademicYearRef:
    pk: str
    name: str
    start_date: date
    end_date: date
    is_active: bool = False

