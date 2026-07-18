"""Django implementation of the site settings repository."""

from core_logic.entities.site_settings import (
    SaveSiteSettingsParams,
    SaveSiteSettingsResult,
    SiteSettingsData,
)
from core_logic.interfaces.settings_repo import ISettingsRepository
from site_settings.models import SiteSettings


class DjangoSettingsRepository(ISettingsRepository):
    def get_site_settings(self) -> SiteSettingsData:
        settings = SiteSettings.get()
        return SiteSettingsData(
            school_name=settings.school_name,
            teacher_name=settings.teacher_name,
            default_subject=settings.default_subject,
            current_academic_year=settings.current_academic_year,
            points_scale=settings.points_scale,
            default_variants_count=settings.default_variants_count,
            logo=settings.logo,
            pdf_font_size=settings.pdf_font_size,
            pdf_margin_top=settings.pdf_margin_top,
            pdf_margin_bottom=settings.pdf_margin_bottom,
        )

    def save_site_settings(
        self,
        params: SaveSiteSettingsParams,
    ) -> SaveSiteSettingsResult:
        settings = SiteSettings.get()
        settings.school_name = params.school_name
        settings.teacher_name = params.teacher_name
        settings.default_subject = params.default_subject
        settings.current_academic_year = params.current_academic_year
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
