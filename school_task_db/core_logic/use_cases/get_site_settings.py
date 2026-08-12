"""Get site settings."""

from core_logic.entities.site_settings import SiteSettingsData
from core_logic.interfaces.site_settings_query_repo import (
    ISiteSettingsQueryRepository,
)


class GetSiteSettingsUseCase:
    def __init__(self, settings_repo: ISiteSettingsQueryRepository):
        self.settings_repo = settings_repo

    def execute(self) -> SiteSettingsData:
        return self.settings_repo.get_site_settings()
