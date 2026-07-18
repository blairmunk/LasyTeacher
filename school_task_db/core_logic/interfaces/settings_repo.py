"""Site settings repository interface."""

from abc import ABC, abstractmethod

from core_logic.entities.site_settings import (
    SaveSiteSettingsParams,
    SaveSiteSettingsResult,
    SiteSettingsData,
)


class ISettingsRepository(ABC):
    @abstractmethod
    def get_site_settings(self) -> SiteSettingsData:
        """Return singleton site settings."""

    @abstractmethod
    def save_site_settings(
        self,
        params: SaveSiteSettingsParams,
    ) -> SaveSiteSettingsResult:
        """Update singleton site settings."""
