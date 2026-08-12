"""Django read adapter for singleton site settings."""

from core_logic.entities.site_settings import SiteSettingsData
from core_logic.interfaces.site_settings_query_repo import (
    ISiteSettingsQueryRepository,
)
from site_settings.models import SiteSettings


class DjangoSiteSettingsQueryRepository(ISiteSettingsQueryRepository):
    def get_site_settings(self) -> SiteSettingsData:
        settings = SiteSettings.get()
        return SiteSettingsData(
            school_name=settings.school_name,
            teacher_name=settings.teacher_name,
            default_subject=settings.default_subject,
            points_scale=settings.points_scale,
            default_variants_count=settings.default_variants_count,
            logo=settings.logo,
            pdf_font_size=settings.pdf_font_size,
            pdf_margin_top=settings.pdf_margin_top,
            pdf_margin_bottom=settings.pdf_margin_bottom,
        )
