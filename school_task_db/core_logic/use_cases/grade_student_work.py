"""Use case for saving a checked student work."""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from core_logic.interfaces.event_repo import (
    GradeParticipationParams,
    GradeParticipationResult,
    IEventRepository,
)
from core_logic.interfaces.attempt_snapshot_repo import (
    IAttemptSnapshotRepository,
)
from core_logic.interfaces.review_repo import IReviewRepository
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.services.grading_service import GradingService
from core_logic.value_objects.mark_validation import validate_mark_values


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


@dataclass(frozen=True)
class GradeStudentWorkResult:
    status: str
    grade: Optional[GradeParticipationResult] = None
    errors: tuple[str, ...] = ()
    attempt_snapshot_id: str = ''


class GradeStudentWorkUseCase:
    def __init__(
        self,
        event_repo: IEventRepository,
        review_repo: IReviewRepository,
        grading_service: GradingService,
        transaction_manager: ITransactionManager,
        attempt_snapshot_repo: IAttemptSnapshotRepository | None = None,
    ):
        self.event_repo = event_repo
        self.review_repo = review_repo
        self.grading_service = grading_service
        self.transaction_manager = transaction_manager
        self.attempt_snapshot_repo = attempt_snapshot_repo

    def execute(self, request: GradeStudentWorkRequest) -> GradeStudentWorkResult:
        checked_by = self.grading_service.checked_by_name(
            display_name=request.checked_by_display_name,
            username=request.checked_by_username,
        )
        with self.transaction_manager.atomic():
            variant_tasks = self.review_repo.get_variant_tasks(
                request.participation_id,
            )
            task_scores = request.task_scores
            points = request.points
            max_points = request.max_points
            if variant_tasks and request.task_scores is not None:
                normalized_scores = self.grading_service.normalize_task_scores(
                    variant_tasks,
                    request.task_scores,
                )
                task_scores = normalized_scores.task_scores
                points = normalized_scores.points
                max_points = normalized_scores.max_points
            try:
                validate_mark_values(
                    score=request.score,
                    points=points,
                    max_points=max_points,
                )
            except ValueError as error:
                return GradeStudentWorkResult(
                    status='invalid',
                    errors=(str(error),),
                )
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
            grade = self.event_repo.save_participation_grade(
                GradeParticipationParams(
                    participation_id=request.participation_id,
                    score=request.score,
                    points=points,
                    max_points=max_points,
                    teacher_comment=request.teacher_comment,
                    mistakes_analysis=request.mistakes_analysis,
                    recommendations=request.recommendations,
                    checked_by=checked_by,
                    work_scan=request.work_scan,
                    task_scores=task_scores,
                    is_retake=request.is_retake,
                    is_excellent=request.is_excellent,
                    needs_attention=request.needs_attention,
                    event_status=event_status,
                )
            )
            attempt_snapshot_id = ''
            if self.attempt_snapshot_repo is not None:
                attempt_snapshot = self.attempt_snapshot_repo.capture_mark(
                    grade.mark_id,
                )
                attempt_snapshot_id = attempt_snapshot.pk
            return GradeStudentWorkResult(
                status='saved',
                grade=grade,
                attempt_snapshot_id=attempt_snapshot_id,
            )
