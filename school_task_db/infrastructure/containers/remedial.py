"""Remedial workflow wiring for the application dependency container."""

from core_logic.services.remedial_service import RemedialService
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
)
from core_logic.use_cases.create_remedial_wizard_work import (
    CreateRemedialWizardWorkUseCase,
)
from core_logic.use_cases.create_student_remedial_variant import (
    CreateStudentRemedialVariantUseCase,
)
from core_logic.use_cases.get_remedial_event_preview import (
    GetRemedialEventPreviewUseCase,
)
from core_logic.use_cases.get_remedial_sheet_data import (
    GetRemedialSheetDataUseCase,
)
from core_logic.use_cases.get_remedial_wizard_preview import (
    GetRemedialWizardPreviewUseCase,
)
from core_logic.use_cases.get_remedial_wizard_start import (
    GetRemedialWizardStartUseCase,
)
from core_logic.use_cases.get_student_remedial_work import (
    GetStudentRemedialWorkUseCase,
)
from core_logic.use_cases.prepare_remedial_from_event_submission import (
    PrepareRemedialFromEventSubmissionUseCase,
)
from core_logic.use_cases.prepare_remedial_wizard_submission import (
    PrepareRemedialWizardCreateSubmissionUseCase,
    PrepareRemedialWizardPreviewSubmissionUseCase,
)
from core_logic.use_cases.prepare_student_remedial_submission import (
    PrepareStudentRemedialSubmissionUseCase,
)
from infrastructure.repositories.django_remedial_sheet_repo import (
    DjangoRemedialSheetRepository,
)
from infrastructure.repositories.django_remedial_source_repo import (
    DjangoRemedialSourceRepository,
)
from infrastructure.repositories.django_remedial_task_group_repo import (
    DjangoRemedialTaskGroupRepository,
)
from infrastructure.repositories.django_student_remedial_repo import (
    DjangoStudentRemedialRepository,
)


class RemedialCompositionMixin:
    """Owns individual remedial work orchestration and data adapters."""

    def _initialize_remedial_composition(self):
        self._student_remedial_repo = None
        self._remedial_sheet_repo = None
        self._remedial_task_group_repo = None
        self._remedial_source_repo = None

    @property
    def student_remedial_repo(self):
        if self._student_remedial_repo is None:
            self._student_remedial_repo = DjangoStudentRemedialRepository()
        return self._student_remedial_repo

    @property
    def remedial_sheet_repo(self):
        if self._remedial_sheet_repo is None:
            self._remedial_sheet_repo = DjangoRemedialSheetRepository()
        return self._remedial_sheet_repo

    @property
    def remedial_task_group_repo(self):
        if self._remedial_task_group_repo is None:
            self._remedial_task_group_repo = (
                DjangoRemedialTaskGroupRepository()
            )
        return self._remedial_task_group_repo

    @property
    def remedial_source_repo(self):
        if self._remedial_source_repo is None:
            self._remedial_source_repo = DjangoRemedialSourceRepository()
        return self._remedial_source_repo

    def remedial_service(self):
        return RemedialService(
            student_remedial_repo=self.student_remedial_repo,
            student_profile_repo=self.student_profile_repo,
            task_repo=self.task_selection_repo,
            task_group_repo=self.remedial_task_group_repo,
            remedial_source_repo=self.remedial_source_repo,
        )

    def create_remedial_from_event_use_case(self):
        return CreateRemedialFromEventUseCase(
            remedial_service=self.remedial_service(),
            task_repo=self.task_selection_repo,
            work_repo=self.work_variant_creation_repo,
            event_repo=self.event_read_repo,
            event_write_repo=self.event_write_repo,
            event_participation_repo=self.event_participation_repo,
            event_attempt_repo=self.event_attempt_repo,
            transaction_manager=self.transaction_manager,
        )

    def create_student_remedial_variant_use_case(self):
        return CreateStudentRemedialVariantUseCase(
            student_repo=self.student_catalog_repo,
            student_learning_repo=self.student_remedial_repo,
            task_repo=self.task_selection_repo,
            work_repo=self.work_variant_creation_repo,
        )

    def create_remedial_wizard_work_use_case(self):
        return CreateRemedialWizardWorkUseCase(
            student_repo=self.student_group_catalog_repo,
            task_repo=self.task_selection_repo,
            work_repo=self.work_variant_creation_repo,
            event_write_repo=self.event_write_repo,
            event_participation_repo=self.event_participation_repo,
            transaction_manager=self.transaction_manager,
        )

    def get_remedial_event_preview_use_case(self):
        return GetRemedialEventPreviewUseCase(
            event_repo=self.event_read_repo,
            event_attempt_repo=self.event_attempt_repo,
        )

    def get_remedial_wizard_preview_use_case(self):
        return GetRemedialWizardPreviewUseCase(
            student_learning_repo=self.student_remedial_repo,
        )

    def get_remedial_wizard_start_use_case(self):
        return GetRemedialWizardStartUseCase(
            student_repo=self.student_group_catalog_repo,
        )

    def get_student_remedial_work_use_case(self):
        return GetStudentRemedialWorkUseCase(
            student_learning_repo=self.student_remedial_repo,
        )

    def prepare_remedial_from_event_submission_use_case(self):
        return PrepareRemedialFromEventSubmissionUseCase()

    def prepare_remedial_wizard_preview_submission_use_case(self):
        return PrepareRemedialWizardPreviewSubmissionUseCase()

    def prepare_remedial_wizard_create_submission_use_case(self):
        return PrepareRemedialWizardCreateSubmissionUseCase()

    def prepare_student_remedial_submission_use_case(self):
        return PrepareStudentRemedialSubmissionUseCase()

    def get_remedial_sheet_data_use_case(self):
        return GetRemedialSheetDataUseCase(
            remedial_repo=self.remedial_sheet_repo,
        )
