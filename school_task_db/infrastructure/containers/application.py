"""Application shell wiring for the dependency container."""

from core_logic.use_cases.get_dashboard_summary import GetDashboardSummaryUseCase
from core_logic.use_cases.get_global_search import GetGlobalSearchUseCase
from core_logic.use_cases.get_import_views import (
    GetImportHistoryUseCase,
    GetImportPageUseCase,
)
from core_logic.use_cases.get_site_settings import GetSiteSettingsUseCase
from core_logic.use_cases.save_site_settings import SaveSiteSettingsUseCase
from infrastructure.forms.core_forms import CoreFormAdapter
from infrastructure.forms.settings_forms import SettingsFormAdapter
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


class ApplicationCompositionMixin:
    """Owns application-level navigation, search, and settings wiring."""

    def _initialize_application_composition(self):
        self._dashboard_summary_repo = None
        self._global_search_repo = None
        self._import_log_repo = None
        self._site_settings_query_repo = None
        self._site_settings_command_repo = None
        self._core_form_adapter = None
        self._settings_form_adapter = None

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
    def settings_form_adapter(self):
        if self._settings_form_adapter is None:
            self._settings_form_adapter = SettingsFormAdapter()
        return self._settings_form_adapter

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
