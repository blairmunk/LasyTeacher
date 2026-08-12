"""Django command adapter for singleton site settings."""

from core_logic.entities.site_settings import (
    SaveSiteSettingsParams,
    SaveSiteSettingsResult,
)
from core_logic.interfaces.site_settings_command_repo import (
    ISiteSettingsCommandRepository,
)
from site_settings.models import SiteSettings


class DjangoSiteSettingsCommandRepository(ISiteSettingsCommandRepository):
    def save_site_settings(
        self,
        params: SaveSiteSettingsParams,
    ) -> SaveSiteSettingsResult:
        settings = SiteSettings.get()
        settings.school_name = params.school_name
        settings.teacher_name = params.teacher_name
        settings.default_subject = params.default_subject
        settings.points_scale = params.points_scale
        settings.default_variants_count = params.default_variants_count
        settings.pdf_font_size = params.pdf_font_size
        settings.pdf_margin_top = params.pdf_margin_top
        settings.pdf_margin_bottom = params.pdf_margin_bottom

        if params.clear_logo:
            settings.logo.delete(save=False)
            settings.logo = None
        elif params.logo:
            settings.logo = params.logo

        settings.save()
        return SaveSiteSettingsResult(status='saved')
