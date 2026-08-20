"""Student and academic year wiring for the dependency container."""

from core_logic.services.analytics_service import StudentAnalyticsService
from core_logic.use_cases.activate_academic_year import (
    ActivateAcademicYearUseCase,
)
from core_logic.use_cases.get_academic_year_list import (
    GetAcademicYearListUseCase,
)
from core_logic.use_cases.get_student_detail import GetStudentDetailUseCase
from core_logic.use_cases.get_student_group_detail import (
    GetStudentGroupDetailUseCase,
)
from core_logic.use_cases.get_student_group_list import GetStudentGroupListUseCase
from core_logic.use_cases.get_student_list import GetStudentListUseCase
from core_logic.use_cases.get_student_profile import GetStudentProfileUseCase
from core_logic.use_cases.import_students import ImportStudentsUseCase
from core_logic.use_cases.resolve_academic_year import ResolveAcademicYearUseCase
from core_logic.use_cases.save_student import (
    CreateStudentGroupUseCase,
    CreateStudentUseCase,
    UpdateStudentGroupUseCase,
    UpdateStudentUseCase,
)
from infrastructure.forms.student_forms import StudentFormAdapter
from infrastructure.repositories.django_academic_year_activation_repo import (
    DjangoAcademicYearActivationRepository,
)
from infrastructure.repositories.django_academic_year_catalog_repo import (
    DjangoAcademicYearCatalogRepository,
)
from infrastructure.repositories.django_student_catalog_repo import (
    DjangoStudentCatalogRepository,
)
from infrastructure.repositories.django_student_command_repo import (
    DjangoStudentCommandRepository,
)
from infrastructure.repositories.django_student_group_catalog_repo import (
    DjangoStudentGroupCatalogRepository,
)
from infrastructure.repositories.django_student_group_command_repo import (
    DjangoStudentGroupCommandRepository,
)
from infrastructure.repositories.django_student_import_command_repo import (
    DjangoStudentImportCommandRepository,
)
from infrastructure.repositories.django_student_import_snapshot_repo import (
    DjangoStudentImportSnapshotRepository,
)
from infrastructure.repositories.django_student_profile_repo import (
    DjangoStudentProfileRepository,
)


class StudentCompositionMixin:
    """Owns students, groups, imports, and academic year wiring."""

    def _initialize_student_composition(self):
        self._academic_year_catalog_repo = None
        self._academic_year_activation_repo = None
        self._student_catalog_repo = None
        self._student_command_repo = None
        self._student_group_catalog_repo = None
        self._student_group_command_repo = None
        self._student_import_snapshot_repo = None
        self._student_import_command_repo = None
        self._student_profile_repo = None
        self._student_form_adapter = None

    @property
    def academic_year_catalog_repo(self):
        if self._academic_year_catalog_repo is None:
            self._academic_year_catalog_repo = (
                DjangoAcademicYearCatalogRepository()
            )
        return self._academic_year_catalog_repo

    @property
    def academic_year_activation_repo(self):
        if self._academic_year_activation_repo is None:
            self._academic_year_activation_repo = (
                DjangoAcademicYearActivationRepository()
            )
        return self._academic_year_activation_repo

    @property
    def student_catalog_repo(self):
        if self._student_catalog_repo is None:
            self._student_catalog_repo = DjangoStudentCatalogRepository()
        return self._student_catalog_repo

    @property
    def student_command_repo(self):
        if self._student_command_repo is None:
            self._student_command_repo = DjangoStudentCommandRepository()
        return self._student_command_repo

    @property
    def student_group_catalog_repo(self):
        if self._student_group_catalog_repo is None:
            self._student_group_catalog_repo = (
                DjangoStudentGroupCatalogRepository()
            )
        return self._student_group_catalog_repo

    @property
    def student_group_command_repo(self):
        if self._student_group_command_repo is None:
            self._student_group_command_repo = (
                DjangoStudentGroupCommandRepository()
            )
        return self._student_group_command_repo

    @property
    def student_import_snapshot_repo(self):
        if self._student_import_snapshot_repo is None:
            self._student_import_snapshot_repo = (
                DjangoStudentImportSnapshotRepository()
            )
        return self._student_import_snapshot_repo

    @property
    def student_import_command_repo(self):
        if self._student_import_command_repo is None:
            self._student_import_command_repo = (
                DjangoStudentImportCommandRepository()
            )
        return self._student_import_command_repo

    @property
    def student_profile_repo(self):
        if self._student_profile_repo is None:
            self._student_profile_repo = DjangoStudentProfileRepository()
        return self._student_profile_repo

    @property
    def student_form_adapter(self):
        if self._student_form_adapter is None:
            self._student_form_adapter = StudentFormAdapter()
        return self._student_form_adapter

    def analytics_service(self):
        return StudentAnalyticsService()

    def get_student_profile_use_case(self):
        return GetStudentProfileUseCase(
            student_repo=self.student_catalog_repo,
            student_learning_repo=self.student_profile_repo,
            analytics_service=self.analytics_service(),
        )

    def get_student_detail_use_case(self):
        return GetStudentDetailUseCase(
            student_repo=self.student_catalog_repo,
        )

    def get_student_group_detail_use_case(self):
        return GetStudentGroupDetailUseCase(
            student_repo=self.student_group_catalog_repo,
        )

    def get_student_list_use_case(self):
        return GetStudentListUseCase(
            student_repo=self.student_catalog_repo,
        )

    def resolve_academic_year_use_case(self):
        return ResolveAcademicYearUseCase(
            academic_year_repo=self.academic_year_catalog_repo,
        )

    def get_academic_year_list_use_case(self):
        return GetAcademicYearListUseCase(
            academic_year_repo=self.academic_year_catalog_repo,
        )

    def activate_academic_year_use_case(self):
        return ActivateAcademicYearUseCase(
            academic_year_repo=self.academic_year_activation_repo,
        )

    def get_student_group_list_use_case(self):
        return GetStudentGroupListUseCase(
            student_repo=self.student_group_catalog_repo,
        )

    def create_student_use_case(self):
        return CreateStudentUseCase(
            student_repo=self.student_command_repo,
        )

    def update_student_use_case(self):
        return UpdateStudentUseCase(
            student_repo=self.student_command_repo,
        )

    def create_student_group_use_case(self):
        return CreateStudentGroupUseCase(
            student_repo=self.student_group_command_repo,
        )

    def update_student_group_use_case(self):
        return UpdateStudentGroupUseCase(
            student_repo=self.student_group_command_repo,
        )

    def import_students_use_case(self):
        return ImportStudentsUseCase(
            snapshot_repo=self.student_import_snapshot_repo,
            command_repo=self.student_import_command_repo,
            transaction_manager=self.transaction_manager,
        )
