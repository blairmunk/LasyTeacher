"""Student-related domain entities."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class StudentLevel(Enum):
    WEAK = 'weak'
    MEDIUM = 'medium'
    STRONG = 'strong'

    @property
    def label_ru(self) -> str:
        return {
            self.WEAK: 'Слабый',
            self.MEDIUM: 'Средний',
            self.STRONG: 'Сильный',
        }[self]


@dataclass(frozen=True)
class TaskResult:
    """A student's result for one task."""

    task_id: str
    points: Optional[float] = None
    max_points: Optional[float] = None
    group_id: Optional[str] = None
    group_name: str = ''

