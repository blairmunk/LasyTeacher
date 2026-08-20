"""Review and grading wiring for the application dependency container."""

from core_logic.services.grading_service import GradingService
from core_logic.services.review_service import ReviewService
from core_logic.use_cases.calculate_review_score import CalculateReviewScoreUseCase
from core_logic.use_cases.finalize_review_event import FinalizeReviewEventUseCase
from core_logic.use_cases.get_event_review import GetEventReviewUseCase
from core_logic.use_cases.get_participation_review import (
    GetParticipationReviewUseCase,
)
from core_logic.use_cases.get_recent_review_sessions import (
    GetRecentReviewSessionsUseCase,
)
from core_logic.use_cases.get_review_dashboard import GetReviewDashboardUseCase
from core_logic.use_cases.get_review_save_navigation import (
    GetReviewSaveNavigationUseCase,
)
from core_logic.use_cases.grade_student_work import GradeStudentWorkUseCase
from core_logic.use_cases.prepare_participation_review_submission import (
    PrepareParticipationReviewSubmissionUseCase,
)
from core_logic.use_cases.sync_review_session import SyncReviewSessionUseCase
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentUseCase,
)
from core_logic.use_cases.validate_review_work_scan import (
    ValidateReviewWorkScanUseCase,
)
from infrastructure.forms.review_forms import ReviewFormAdapter
from infrastructure.repositories.django_attempt_snapshot_repo import (
    DjangoAttemptSnapshotRepository,
)
from infrastructure.repositories.django_participation_grading_repo import (
    DjangoParticipationGradingRepository,
)
from infrastructure.repositories.django_review_overview_repo import (
    DjangoReviewOverviewRepository,
)
from infrastructure.repositories.django_review_session_command_repo import (
    DjangoReviewSessionCommandRepository,
)
from infrastructure.repositories.django_review_session_query_repo import (
    DjangoReviewSessionQueryRepository,
)
from infrastructure.repositories.django_review_task_repo import (
    DjangoReviewTaskRepository,
)
from infrastructure.repositories.django_review_workflow_repo import (
    DjangoReviewWorkflowRepository,
)


class ReviewCompositionMixin:
    """Owns grading, attempt snapshots, and review workflow wiring."""

    def _initialize_review_composition(self):
        self._attempt_snapshot_repo = None
        self._participation_grading_repo = None
        self._review_overview_repo = None
        self._review_workflow_repo = None
        self._review_session_query_repo = None
        self._review_session_command_repo = None
        self._review_task_repo = None
        self._review_form_adapter = None

    @property
    def attempt_snapshot_repo(self):
        if self._attempt_snapshot_repo is None:
            self._attempt_snapshot_repo = DjangoAttemptSnapshotRepository()
        return self._attempt_snapshot_repo

    @property
    def participation_grading_repo(self):
        if self._participation_grading_repo is None:
            self._participation_grading_repo = (
                DjangoParticipationGradingRepository()
            )
        return self._participation_grading_repo

    @property
    def review_overview_repo(self):
        if self._review_overview_repo is None:
            self._review_overview_repo = DjangoReviewOverviewRepository()
        return self._review_overview_repo

    @property
    def review_workflow_repo(self):
        if self._review_workflow_repo is None:
            self._review_workflow_repo = DjangoReviewWorkflowRepository()
        return self._review_workflow_repo

    @property
    def review_session_query_repo(self):
        if self._review_session_query_repo is None:
            self._review_session_query_repo = (
                DjangoReviewSessionQueryRepository()
            )
        return self._review_session_query_repo

    @property
    def review_session_command_repo(self):
        if self._review_session_command_repo is None:
            self._review_session_command_repo = (
                DjangoReviewSessionCommandRepository()
            )
        return self._review_session_command_repo

    @property
    def review_task_repo(self):
        if self._review_task_repo is None:
            self._review_task_repo = DjangoReviewTaskRepository()
        return self._review_task_repo

    @property
    def review_form_adapter(self):
        if self._review_form_adapter is None:
            self._review_form_adapter = ReviewFormAdapter()
        return self._review_form_adapter

    def grading_service(self):
        return GradingService()

    def review_service(self):
        return ReviewService()

    def grade_student_work_use_case(self):
        return GradeStudentWorkUseCase(
            grading_repo=self.participation_grading_repo,
            review_task_repo=self.review_task_repo,
            grading_service=self.grading_service(),
            transaction_manager=self.transaction_manager,
            attempt_snapshot_repo=self.attempt_snapshot_repo,
        )

    def get_participation_review_use_case(self):
        return GetParticipationReviewUseCase(
            review_repo=self.review_workflow_repo,
            review_task_repo=self.review_task_repo,
            review_service=self.review_service(),
        )

    def get_review_dashboard_use_case(self):
        return GetReviewDashboardUseCase(
            review_repo=self.review_overview_repo,
            review_service=self.review_service(),
        )

    def get_event_review_use_case(self):
        return GetEventReviewUseCase(
            event_repo=self.event_read_repo,
            review_repo=self.review_overview_repo,
            review_service=self.review_service(),
        )

    def calculate_review_score_use_case(self):
        return CalculateReviewScoreUseCase(
            review_service=self.review_service(),
        )

    def finalize_review_event_use_case(self):
        return FinalizeReviewEventUseCase(
            review_repo=self.review_workflow_repo,
        )

    def toggle_participation_absent_use_case(self):
        return ToggleParticipationAbsentUseCase(
            review_repo=self.review_workflow_repo,
        )

    def prepare_participation_review_submission_use_case(self):
        return PrepareParticipationReviewSubmissionUseCase(
            review_service=self.review_service(),
        )

    def validate_review_work_scan_use_case(self):
        return ValidateReviewWorkScanUseCase(
            review_service=self.review_service(),
        )

    def get_review_save_navigation_use_case(self):
        return GetReviewSaveNavigationUseCase(
            review_repo=self.review_workflow_repo,
        )

    def get_recent_review_sessions_use_case(self):
        return GetRecentReviewSessionsUseCase(
            session_repo=self.review_session_query_repo,
        )

    def sync_review_session_use_case(self):
        return SyncReviewSessionUseCase(
            session_repo=self.review_session_command_repo,
        )
