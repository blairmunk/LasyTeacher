"""Event-related domain entities."""

from dataclasses import dataclass
from typing import Any, Dict, Optional


def _same_pk(left_id: str, other: Any) -> bool:
    other_id = getattr(other, 'pk', getattr(other, 'id', None))
    return other_id is not None and str(left_id) == str(other_id)


@dataclass(frozen=True)
class WorkSummary:
    id: str
    name: str

    @property
    def pk(self) -> str:
        return self.id

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class VariantSummary:
    id: str
    number: int

    @property
    def pk(self) -> str:
        return self.id

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class StudentSummary:
    id: str
    full_name: str

    @property
    def pk(self) -> str:
        return self.id

    def get_full_name(self) -> str:
        return self.full_name

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class EventEntity:
    id: str
    name: str
    work_id: str
    work_name: str
    course_id: Optional[str] = None

    @property
    def pk(self) -> str:
        return self.id

    def __eq__(self, other):
        return _same_pk(self.id, other)


@dataclass(frozen=True)
class MarkEntity:
    student_id: str
    event_id: str
    score: Optional[int] = None


@dataclass(frozen=True)
class ParticipationMarkData:
    student: StudentSummary
    variant: Optional[VariantSummary]
    score: Optional[int] = None
    points: Optional[float] = None
    max_points: Optional[float] = None
    task_scores: Dict[str, dict] = None
