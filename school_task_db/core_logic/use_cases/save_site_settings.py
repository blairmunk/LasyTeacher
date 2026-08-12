"""Save site settings."""

from core_logic.entities.site_settings import (
    SaveSiteSettingsParams,
    SaveSiteSettingsResult,
)
from core_logic.interfaces.site_settings_command_repo import (
    ISiteSettingsCommandRepository,
)


class SaveSiteSettingsUseCase:
    def __init__(self, settings_repo: ISiteSettingsCommandRepository):
        self.settings_repo = settings_repo

    def execute(
        self,
        params: SaveSiteSettingsParams,
    ) -> SaveSiteSettingsResult:
        return self.settings_repo.save_site_settings(params)
