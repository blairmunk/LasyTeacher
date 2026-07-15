"""Small dependency container for application use cases."""

from core_logic.services.analytics_service import StudentAnalyticsService
from core_logic.services.event_service import EventService
from core_logic.services.grading_service import GradingService
from core_logic.services.remedial_service import RemedialService
from core_logic.services.review_service import ReviewService
from core_logic.services.work_service import WorkService
from core_logic.use_cases.add_event_participants import AddEventParticipantsUseCase
from core_logic.use_cases.assign_event_variants import AssignEventVariantsUseCase
from core_logic.use_cases.assign_single_event_variant import (
    AssignSingleEventVariantUseCase,
)
from core_logic.use_cases.bulk_delete_variants import BulkDeleteVariantsUseCase
from core_logic.use_cases.calculate_review_score import CalculateReviewScoreUseCase
from core_logic.use_cases.change_event_status import ChangeEventStatusUseCase
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
)
from core_logic.use_cases.create_student_remedial_variant import (
    CreateStudentRemedialVariantUseCase,
)
from core_logic.use_cases.create_remedial_wizard_work import (
    CreateRemedialWizardWorkUseCase,
)
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansUseCase,
)
from core_logic.use_cases.delete_variant import DeleteVariantUseCase
from core_logic.use_cases.finalize_review_event import FinalizeReviewEventUseCase
from core_logic.use_cases.generate_work_variants import GenerateWorkVariantsUseCase
from core_logic.use_cases.generate_remedial_sheet_document import (
    GenerateRemedialSheetDocumentUseCase,
)
from core_logic.use_cases.generate_work_document import GenerateWorkDocumentUseCase
from core_logic.use_cases.grade_student_work import GradeStudentWorkUseCase
from core_logic.use_cases.get_participation_review import (
    GetParticipationReviewUseCase,
)
from core_logic.use_cases.get_event_review import GetEventReviewUseCase
from core_logic.use_cases.get_event_detail import GetEventDetailUseCase
from core_logic.use_cases.get_event_list import GetEventListUseCase
from core_logic.use_cases.get_event_participant_selection import (
    GetEventParticipantSelectionUseCase,
)
from core_logic.use_cases.get_generated_document_file import (
    GetGeneratedDocumentFileUseCase,
)
from core_logic.use_cases.get_orphan_variant_list import GetOrphanVariantListUseCase
from core_logic.use_cases.get_remedial_event_preview import (
    GetRemedialEventPreviewUseCase,
)
from core_logic.use_cases.get_remedial_sheet_data import (
    GetRemedialSheetDataUseCase,
)
from core_logic.use_cases.get_recent_review_sessions import (
    GetRecentReviewSessionsUseCase,
)
from core_logic.use_cases.get_remedial_wizard_preview import (
    GetRemedialWizardPreviewUseCase,
)
from core_logic.use_cases.get_review_dashboard import GetReviewDashboardUseCase
from core_logic.use_cases.get_review_save_navigation import (
    GetReviewSaveNavigationUseCase,
)
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from core_logic.use_cases.get_student_remedial_work import (
    GetStudentRemedialWorkUseCase,
)
from core_logic.use_cases.get_variant_detail import GetVariantDetailUseCase
from core_logic.use_cases.get_variant_generation_placeholder import (
    GetVariantGenerationPlaceholderUseCase,
)
from core_logic.use_cases.get_variant_list import GetVariantListUseCase
from core_logic.use_cases.get_work_detail import GetWorkDetailUseCase
from core_logic.use_cases.get_work_form_data import GetWorkFormDataUseCase
from core_logic.use_cases.get_work_list import GetWorkListUseCase
from core_logic.use_cases.get_variant_delete_info import GetVariantDeleteInfoUseCase
from core_logic.use_cases.prepare_participation_review_submission import (
    PrepareParticipationReviewSubmissionUseCase,
)
from core_logic.use_cases.sync_review_session import SyncReviewSessionUseCase
from core_logic.use_cases.sync_work_analog_groups import SyncWorkAnalogGroupsUseCase
from core_logic.use_cases.toggle_participation_absent import (
    ToggleParticipationAbsentUseCase,
)
from core_logic.use_cases.validate_review_work_scan import ValidateReviewWorkScanUseCase
from infrastructure.repositories.django_event_repo import DjangoEventRepository
from infrastructure.repositories.django_review_repo import DjangoReviewRepository
from infrastructure.repositories.django_student_repo import DjangoStudentRepository
from infrastructure.repositories.django_task_repo import DjangoTaskRepository
from infrastructure.repositories.django_work_repo import DjangoWorkRepository
from infrastructure.services.document_generation_service import (
    DjangoDocumentGenerationService,
)
from infrastructure.forms.work_forms import WorkFormAdapter


class Container:
    """Wires pure use cases to Django infrastructure adapters."""

    def __init__(self):
        self._student_repo = None
        self._task_repo = None
        self._work_repo = None
        self._event_repo = None
        self._review_repo = None
        self._work_form_adapter = None
        self._document_generation_service = None

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

    @property
    def work_form_adapter(self):
        if self._work_form_adapter is None:
            self._work_form_adapter = WorkFormAdapter()
        return self._work_form_adapter

    @property
    def document_generation_service(self):
        if self._document_generation_service is None:
            self._document_generation_service = DjangoDocumentGenerationService(
                get_remedial_sheet_data_use_case=(
                    self.get_remedial_sheet_data_use_case()
                ),
            )
        return self._document_generation_service

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

    def event_service(self):
        return EventService()

    def review_service(self):
        return ReviewService()

    def work_service(self):
        return WorkService()

    def create_remedial_from_event_use_case(self):
        return CreateRemedialFromEventUseCase(
            remedial_service=self.remedial_service(),
            task_repo=self.task_repo,
            work_repo=self.work_repo,
            event_repo=self.event_repo,
        )

    def create_student_remedial_variant_use_case(self):
        return CreateStudentRemedialVariantUseCase(
            student_repo=self.student_repo,
            task_repo=self.task_repo,
            work_repo=self.work_repo,
        )

    def create_remedial_wizard_work_use_case(self):
        return CreateRemedialWizardWorkUseCase(
            student_repo=self.student_repo,
            task_repo=self.task_repo,
            work_repo=self.work_repo,
            event_repo=self.event_repo,
        )

    def get_remedial_event_preview_use_case(self):
        return GetRemedialEventPreviewUseCase(
            event_repo=self.event_repo,
        )

    def get_remedial_wizard_preview_use_case(self):
        return GetRemedialWizardPreviewUseCase(
            student_repo=self.student_repo,
        )

    def get_student_profile_use_case(self):
        return GetStudentProfileUseCase(
            student_repo=self.student_repo,
            analytics_service=self.analytics_service(),
        )

    def get_student_remedial_work_use_case(self):
        return GetStudentRemedialWorkUseCase(
            student_repo=self.student_repo,
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

    def get_review_dashboard_use_case(self):
        return GetReviewDashboardUseCase(
            review_repo=self.review_repo,
            review_service=self.review_service(),
        )

    def get_event_review_use_case(self):
        return GetEventReviewUseCase(
            review_repo=self.review_repo,
            review_service=self.review_service(),
        )

    def get_event_list_use_case(self):
        return GetEventListUseCase(
            event_repo=self.event_repo,
            event_service=self.event_service(),
        )

    def get_event_detail_use_case(self):
        return GetEventDetailUseCase(
            event_repo=self.event_repo,
            event_service=self.event_service(),
        )

    def get_event_participant_selection_use_case(self):
        return GetEventParticipantSelectionUseCase(
            event_repo=self.event_repo,
        )

    def add_event_participants_use_case(self):
        return AddEventParticipantsUseCase(
            event_repo=self.event_repo,
        )

    def assign_event_variants_use_case(self):
        return AssignEventVariantsUseCase(
            event_repo=self.event_repo,
        )

    def assign_single_event_variant_use_case(self):
        return AssignSingleEventVariantUseCase(
            event_repo=self.event_repo,
        )

    def change_event_status_use_case(self):
        return ChangeEventStatusUseCase(
            event_repo=self.event_repo,
            event_service=self.event_service(),
        )

    def calculate_review_score_use_case(self):
        return CalculateReviewScoreUseCase(
            review_service=self.review_service(),
        )

    def finalize_review_event_use_case(self):
        return FinalizeReviewEventUseCase(
            review_repo=self.review_repo,
        )

    def toggle_participation_absent_use_case(self):
        return ToggleParticipationAbsentUseCase(
            review_repo=self.review_repo,
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
            review_repo=self.review_repo,
        )

    def get_recent_review_sessions_use_case(self):
        return GetRecentReviewSessionsUseCase(
            review_repo=self.review_repo,
        )

    def sync_review_session_use_case(self):
        return SyncReviewSessionUseCase(
            review_repo=self.review_repo,
        )

    def get_work_detail_use_case(self):
        return GetWorkDetailUseCase(
            work_repo=self.work_repo,
            work_service=self.work_service(),
        )

    def get_work_list_use_case(self):
        return GetWorkListUseCase(
            work_repo=self.work_repo,
        )

    def get_work_form_data_use_case(self):
        return GetWorkFormDataUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_detail_use_case(self):
        return GetVariantDetailUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_generation_placeholder_use_case(self):
        return GetVariantGenerationPlaceholderUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_list_use_case(self):
        return GetVariantListUseCase(
            work_repo=self.work_repo,
        )

    def get_orphan_variant_list_use_case(self):
        return GetOrphanVariantListUseCase(
            work_repo=self.work_repo,
        )

    def get_remedial_sheet_data_use_case(self):
        return GetRemedialSheetDataUseCase(
            work_repo=self.work_repo,
        )

    def sync_work_analog_groups_use_case(self):
        return SyncWorkAnalogGroupsUseCase(
            work_repo=self.work_repo,
        )

    def generate_work_variants_use_case(self):
        return GenerateWorkVariantsUseCase(
            work_repo=self.work_repo,
        )

    def generate_work_document_use_case(self):
        return GenerateWorkDocumentUseCase(
            document_generation_service=self.document_generation_service,
        )

    def generate_remedial_sheet_document_use_case(self):
        return GenerateRemedialSheetDocumentUseCase(
            document_generation_service=self.document_generation_service,
            work_repo=self.work_repo,
        )

    def get_generated_document_file_use_case(self):
        return GetGeneratedDocumentFileUseCase(
            document_generation_service=self.document_generation_service,
        )

    def create_work_from_orphans_use_case(self):
        return CreateWorkFromOrphansUseCase(
            work_repo=self.work_repo,
        )

    def get_variant_delete_info_use_case(self):
        return GetVariantDeleteInfoUseCase(
            work_repo=self.work_repo,
        )

    def delete_variant_use_case(self):
        return DeleteVariantUseCase(
            work_repo=self.work_repo,
        )

    def bulk_delete_variants_use_case(self):
        return BulkDeleteVariantsUseCase(
            work_repo=self.work_repo,
        )


container = Container()
