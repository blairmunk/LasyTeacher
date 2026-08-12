"""Command repository port for site settings."""

from abc import ABC, abstractmethod

from core_logic.entities.site_settings import (
    SaveSiteSettingsParams,
    SaveSiteSettingsResult,
)


class ISiteSettingsCommandRepository(ABC):
    @abstractmethod
    def save_site_settings(
        self,
        params: SaveSiteSettingsParams,
    ) -> SaveSiteSettingsResult:
        """Update singleton site settings."""
