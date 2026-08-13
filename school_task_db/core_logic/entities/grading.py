"""Command and result data for participation grading."""

from dataclasses import dataclass
from typing import Any, Optional

from core_logic.entities.review import ReviewTaskScoreValue


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
    task_scores: Optional[tuple[ReviewTaskScoreValue, ...]] = None
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
