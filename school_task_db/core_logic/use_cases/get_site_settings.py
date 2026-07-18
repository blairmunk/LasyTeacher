"""Get site settings."""

from core_logic.entities.site_settings import SiteSettingsData
from core_logic.interfaces.settings_repo import ISettingsRepository


class GetSiteSettingsUseCase:
    def __init__(self, settings_repo: ISettingsRepository):
        self.settings_repo = settings_repo

    def execute(self) -> SiteSettingsData:
        return self.settings_repo.get_site_settings()
