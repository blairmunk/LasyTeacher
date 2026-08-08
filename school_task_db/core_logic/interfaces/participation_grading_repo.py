"""Write port for persisting a checked event participation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from core_logic.entities.event import ParticipationGradingContext


@dataclass(frozen=True)
class GradeParticipationParams:
    participation_id: str
    score: Optional[int] = None
    points: Optional[int] = None
    max_points: Optional[int] = None
    teacher_comment: str = ''
    mistakes_analysis: str = ''
    recommendations: str = ''
    checked_by: str = ''
    work_scan: Optional[Any] = None
    task_scores: Optional[Dict[str, dict]] = None
    is_retake: bool = False
    is_excellent: bool = False
    needs_attention: bool = False
    event_status: Optional[str] = None


@dataclass(frozen=True)
class GradeParticipationResult:
    mark_id: str
    participation_id: str
    event_id: str
    student_name: str
    score: Optional[int]
    event_status: str


class IParticipationGradingRepository(ABC):
    @abstractmethod
    def get_participation_grading_context(
        self,
        participation_id: str,
    ) -> ParticipationGradingContext:
        """Lock and return the state needed for grading decisions."""

    @abstractmethod
    def save_participation_grade(
        self,
        params: GradeParticipationParams,
    ) -> GradeParticipationResult:
        """Persist a mark, participation state and optional event status."""

