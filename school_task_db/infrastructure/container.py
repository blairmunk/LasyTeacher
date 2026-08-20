"""Application dependency composition root."""

from core_logic.use_cases.get_codifier_detail import GetCodifierDetailUseCase
from core_logic.use_cases.get_codifier_list import GetCodifierListUseCase
from core_logic.use_cases.get_course_detail import GetCourseDetailUseCase
from core_logic.use_cases.get_course_list import GetCourseListUseCase
from core_logic.use_cases.get_dashboard_summary import GetDashboardSummaryUseCase
from core_logic.use_cases.get_global_search import GetGlobalSearchUseCase
from core_logic.use_cases.get_import_views import (
    GetImportHistoryUseCase,
    GetImportPageUseCase,
)
from core_logic.use_cases.get_site_settings import GetSiteSettingsUseCase
from core_logic.use_cases.get_topic_detail import GetTopicDetailUseCase
from core_logic.use_cases.get_topic_list import GetTopicListUseCase
from core_logic.use_cases.get_topic_subtopics import GetTopicSubtopicsUseCase
from core_logic.use_cases.import_codifier import ImportCodifierUseCase
from core_logic.use_cases.import_curriculum import ImportCurriculumUseCase
from core_logic.use_cases.save_site_settings import SaveSiteSettingsUseCase
from infrastructure.containers.document import DocumentCompositionMixin
from infrastructure.containers.event import EventCompositionMixin
from infrastructure.containers.remedial import RemedialCompositionMixin
from infrastructure.containers.reporting import ReportingCompositionMixin
from infrastructure.containers.review import ReviewCompositionMixin
from infrastructure.containers.student import StudentCompositionMixin
from infrastructure.containers.task import TaskCompositionMixin
from infrastructure.containers.work import WorkCompositionMixin
from infrastructure.forms.codifier_forms import CodifierFormAdapter
from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.curriculum_forms import CurriculumFormAdapter
from infrastructure.forms.settings_forms import SettingsFormAdapter
from infrastructure.repositories.django_codifier_catalog_repo import (
    DjangoCodifierCatalogRepository,
)
from infrastructure.repositories.django_codifier_detail_repo import (
    DjangoCodifierDetailRepository,
)
from infrastructure.repositories.django_codifier_import_repo import (
    DjangoCodifierImportRepository,
)
from infrastructure.repositories.django_course_catalog_repo import (
    DjangoCourseCatalogRepository,
)
from infrastructure.repositories.django_curriculum_import_repo import (
    DjangoCurriculumImportRepository,
)
from infrastructure.repositories.django_dashboard_summary_repo import (
    DjangoDashboardSummaryRepository,
)
from infrastructure.repositories.django_global_search_repo import (
    DjangoGlobalSearchRepository,
)
from infrastructure.repositories.django_import_log_repo import (
    DjangoImportLogRepository,
)
from infrastructure.repositories.django_site_settings_command_repo import (
    DjangoSiteSettingsCommandRepository,
)
from infrastructure.repositories.django_site_settings_query_repo import (
    DjangoSiteSettingsQueryRepository,
)
from infrastructure.repositories.django_topic_catalog_repo import (
    DjangoTopicCatalogRepository,
)
from infrastructure.services.django_transaction_manager import (
    DjangoTransactionManager,
)


class Container(
    DocumentCompositionMixin,
    EventCompositionMixin,
    RemedialCompositionMixin,
    ReportingCompositionMixin,
    ReviewCompositionMixin,
    StudentCompositionMixin,
    TaskCompositionMixin,
    WorkCompositionMixin,
):
    """Wires pure use cases to infrastructure adapters."""

    def __init__(self):
        self._initialize_document_composition()
        self._initialize_event_composition()
        self._initialize_remedial_composition()
        self._initialize_reporting_composition()
        self._initialize_review_composition()
        self._initialize_student_composition()
        self._initialize_task_composition()
        self._initialize_work_composition()
        self._course_catalog_repo = None
        self._topic_catalog_repo = None
        self._curriculum_import_repo = None
        self._codifier_catalog_repo = None
        self._codifier_detail_repo = None
        self._codifier_import_repo = None
        self._dashboard_summary_repo = None
        self._global_search_repo = None
        self._import_log_repo = None
        self._site_settings_query_repo = None
        self._site_settings_command_repo = None
        self._codifier_form_adapter = None
        self._core_form_adapter = None
        self._curriculum_form_adapter = None
        self._settings_form_adapter = None
        self._transaction_manager = None

    @property
    def transaction_manager(self):
        if self._transaction_manager is None:
            self._transaction_manager = DjangoTransactionManager()
        return self._transaction_manager

    @property
    def course_catalog_repo(self):
        if self._course_catalog_repo is None:
            self._course_catalog_repo = DjangoCourseCatalogRepository()
        return self._course_catalog_repo

    @property
    def topic_catalog_repo(self):
        if self._topic_catalog_repo is None:
            self._topic_catalog_repo = DjangoTopicCatalogRepository()
        return self._topic_catalog_repo

    @property
    def codifier_catalog_repo(self):
        if self._codifier_catalog_repo is None:
            self._codifier_catalog_repo = DjangoCodifierCatalogRepository()
        return self._codifier_catalog_repo

    @property
    def codifier_detail_repo(self):
        if self._codifier_detail_repo is None:
            self._codifier_detail_repo = DjangoCodifierDetailRepository()
        return self._codifier_detail_repo

    @property
    def codifier_import_repo(self):
        if self._codifier_import_repo is None:
            self._codifier_import_repo = DjangoCodifierImportRepository()
        return self._codifier_import_repo

    @property
    def curriculum_import_repo(self):
        if self._curriculum_import_repo is None:
            self._curriculum_import_repo = DjangoCurriculumImportRepository()
        return self._curriculum_import_repo

    @property
    def dashboard_summary_repo(self):
        if self._dashboard_summary_repo is None:
            self._dashboard_summary_repo = DjangoDashboardSummaryRepository()
        return self._dashboard_summary_repo

    @property
    def global_search_repo(self):
        if self._global_search_repo is None:
            self._global_search_repo = DjangoGlobalSearchRepository()
        return self._global_search_repo

    @property
    def import_log_repo(self):
        if self._import_log_repo is None:
            self._import_log_repo = DjangoImportLogRepository()
        return self._import_log_repo

    @property
    def site_settings_query_repo(self):
        if self._site_settings_query_repo is None:
            self._site_settings_query_repo = DjangoSiteSettingsQueryRepository()
        return self._site_settings_query_repo

    @property
    def site_settings_command_repo(self):
        if self._site_settings_command_repo is None:
            self._site_settings_command_repo = (
                DjangoSiteSettingsCommandRepository()
            )
        return self._site_settings_command_repo

    @property
    def core_form_adapter(self):
        if self._core_form_adapter is None:
            self._core_form_adapter = CoreFormAdapter()
        return self._core_form_adapter

    @property
    def codifier_form_adapter(self):
        if self._codifier_form_adapter is None:
            self._codifier_form_adapter = CodifierFormAdapter()
        return self._codifier_form_adapter

    @property
    def curriculum_form_adapter(self):
        if self._curriculum_form_adapter is None:
            self._curriculum_form_adapter = CurriculumFormAdapter()
        return self._curriculum_form_adapter

    @property
    def settings_form_adapter(self):
        if self._settings_form_adapter is None:
            self._settings_form_adapter = SettingsFormAdapter()
        return self._settings_form_adapter

    def import_codifier_use_case(self):
        return ImportCodifierUseCase(
            codifier_repo=self.codifier_import_repo,
            transaction_manager=self.transaction_manager,
        )

    def import_curriculum_use_case(self):
        return ImportCurriculumUseCase(
            curriculum_repo=self.curriculum_import_repo,
            transaction_manager=self.transaction_manager,
        )

    def get_course_detail_use_case(self):
        return GetCourseDetailUseCase(
            curriculum_repo=self.course_catalog_repo,
        )

    def get_course_list_use_case(self):
        return GetCourseListUseCase(
            curriculum_repo=self.course_catalog_repo,
        )

    def get_topic_subtopics_use_case(self):
        return GetTopicSubtopicsUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_topic_list_use_case(self):
        return GetTopicListUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_topic_detail_use_case(self):
        return GetTopicDetailUseCase(
            curriculum_repo=self.topic_catalog_repo,
        )

    def get_codifier_list_use_case(self):
        return GetCodifierListUseCase(
            codifier_repo=self.codifier_catalog_repo,
        )

    def get_codifier_detail_use_case(self):
        return GetCodifierDetailUseCase(
            codifier_repo=self.codifier_detail_repo,
        )

    def get_dashboard_summary_use_case(self):
        return GetDashboardSummaryUseCase(
            core_repo=self.dashboard_summary_repo,
        )

    def get_global_search_use_case(self):
        return GetGlobalSearchUseCase(
            core_repo=self.global_search_repo,
        )

    def get_import_page_use_case(self):
        return GetImportPageUseCase(
            core_repo=self.import_log_repo,
        )

    def get_import_history_use_case(self):
        return GetImportHistoryUseCase(
            core_repo=self.import_log_repo,
        )

    def get_site_settings_use_case(self):
        return GetSiteSettingsUseCase(
            settings_repo=self.site_settings_query_repo,
        )

    def save_site_settings_use_case(self):
        return SaveSiteSettingsUseCase(
            settings_repo=self.site_settings_command_repo,
        )


container = Container()
