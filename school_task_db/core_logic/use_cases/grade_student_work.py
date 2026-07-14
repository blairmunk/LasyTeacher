"""Use case for saving a checked student work."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from core_logic.interfaces.event_repo import (
    GradeParticipationParams,
    GradeParticipationResult,
    IEventRepository,
)
from core_logic.services.grading_service import GradingService


@dataclass(frozen=True)
class GradeStudentWorkRequest:
    participation_id: str
    score: Optional[int] = None
    points: Optional[int] = None
    max_points: Optional[int] = None
    teacher_comment: str = ''
    mistakes_analysis: str = ''
    recommendations: str = ''
    checked_by_display_name: str = ''
    checked_by_username: str = ''
    work_scan: Optional[Any] = None
    task_scores: Optional[Dict[str, dict]] = None
    is_retake: bool = False
    is_excellent: bool = False
    needs_attention: bool = False
    sync_event_status: bool = True


class GradeStudentWorkUseCase:
    def __init__(
        self,
        event_repo: IEventRepository,
        grading_service: GradingService,
    ):
        self.event_repo = event_repo
        self.grading_service = grading_service

    def execute(self, request: GradeStudentWorkRequest) -> GradeParticipationResult:
        checked_by = self.grading_service.checked_by_name(
            display_name=request.checked_by_display_name,
            username=request.checked_by_username,
        )
        return self.event_repo.grade_participation(
            GradeParticipationParams(
                participation_id=request.participation_id,
                score=request.score,
                points=request.points,
                max_points=request.max_points,
                teacher_comment=request.teacher_comment,
                mistakes_analysis=request.mistakes_analysis,
                recommendations=request.recommendations,
                checked_by=checked_by,
                work_scan=request.work_scan,
                task_scores=request.task_scores,
                is_retake=request.is_retake,
                is_excellent=request.is_excellent,
                needs_attention=request.needs_attention,
                sync_event_status=request.sync_event_status,
            )
        )
