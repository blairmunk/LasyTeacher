"""Read-only repository port for site settings."""

from abc import ABC, abstractmethod

from core_logic.entities.site_settings import SiteSettingsData


class ISiteSettingsQueryRepository(ABC):
    @abstractmethod
    def get_site_settings(self) -> SiteSettingsData:
        """Return singleton site settings."""
