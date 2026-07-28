"""Use case for saving a checked student work."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from core_logic.interfaces.event_repo import (
    GradeParticipationParams,
    GradeParticipationResult,
    IEventRepository,
)
from core_logic.interfaces.transaction_manager import ITransactionManager
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
        transaction_manager: ITransactionManager,
    ):
        self.event_repo = event_repo
        self.grading_service = grading_service
        self.transaction_manager = transaction_manager

    def execute(self, request: GradeStudentWorkRequest) -> GradeParticipationResult:
        checked_by = self.grading_service.checked_by_name(
            display_name=request.checked_by_display_name,
            username=request.checked_by_username,
        )
        with self.transaction_manager.atomic():
            context = self.event_repo.get_participation_grading_context(
                request.participation_id,
            )
            event_status = None
            if request.sync_event_status:
                event_status = self.grading_service.next_event_status(
                    current_status=context.event_status,
                    active_participants=(
                        context.other_active_participants + 1
                    ),
                    graded_participants=(
                        context.other_graded_participants + 1
                    ),
                )
            return self.event_repo.save_participation_grade(
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
                    event_status=event_status,
                )
            )
