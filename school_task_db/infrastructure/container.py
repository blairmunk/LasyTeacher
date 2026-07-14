"""Small dependency container for application use cases."""

from core_logic.services.analytics_service import StudentAnalyticsService
from core_logic.services.grading_service import GradingService
from core_logic.services.remedial_service import RemedialService
from core_logic.services.review_service import ReviewService
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
)
from core_logic.use_cases.grade_student_work import GradeStudentWorkUseCase
from core_logic.use_cases.get_participation_review import (
    GetParticipationReviewUseCase,
)
from core_logic.use_cases.get_remedial_event_preview import (
    GetRemedialEventPreviewUseCase,
)
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from infrastructure.repositories.django_event_repo import DjangoEventRepository
from infrastructure.repositories.django_review_repo import DjangoReviewRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_task_repo import DjangoTaskRepository
from infrastructure.repositories.django_work_repo import DjangoWorkRepository


class Container:
    """Wires pure use cases to Django infrastructure adapters."""

    def __init__(self):
        self._student_repo = None
        self._task_repo = None
        self._work_repo = None
        self._event_repo = None
        self._review_repo = None

    @property
    def student_repo(self):
        if self._student_repo is None:
            self._student_repo = DjangoStudentRepository()
        return self._student_repo

    @property
    def task_repo(self):
        if self._task_repo is None:
            self._task_repo = DjangoTaskRepository()
        return self._task_repo

    @property
    def work_repo(self):
        if self._work_repo is None:
            self._work_repo = DjangoWorkRepository()
        return self._work_repo

    @property
    def event_repo(self):
        if self._event_repo is None:
            self._event_repo = DjangoEventRepository()
        return self._event_repo

    @property
    def review_repo(self):
        if self._review_repo is None:
            self._review_repo = DjangoReviewRepository()
        return self._review_repo

    def remedial_service(self):
        return RemedialService(
            student_repo=self.student_repo,
            task_repo=self.task_repo,
            work_repo=self.work_repo,
        )

    def analytics_service(self):
        return StudentAnalyticsService()

    def grading_service(self):
        return GradingService()

    def review_service(self):
        return ReviewService()

    def create_remedial_from_event_use_case(self):
        return CreateRemedialFromEventUseCase(
            remedial_service=self.remedial_service(),
            task_repo=self.task_repo,
            work_repo=self.work_repo,
            event_repo=self.event_repo,
        )

    def get_remedial_event_preview_use_case(self):
        return GetRemedialEventPreviewUseCase(
            event_repo=self.event_repo,
        )

    def get_student_profile_use_case(self):
        return GetStudentProfileUseCase(
            student_repo=self.student_repo,
            analytics_service=self.analytics_service(),
        )

    def grade_student_work_use_case(self):
        return GradeStudentWorkUseCase(
            event_repo=self.event_repo,
            grading_service=self.grading_service(),
        )

    def get_participation_review_use_case(self):
        return GetParticipationReviewUseCase(
            review_repo=self.review_repo,
            review_service=self.review_service(),
        )


container = Container()
