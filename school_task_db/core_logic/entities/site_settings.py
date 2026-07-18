"""Site settings DTOs."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SiteSettingsData:
    school_name: str = ''
    teacher_name: str = ''
    default_subject: str = 'Физика'
    current_academic_year: str = '2025-2026'
    points_scale: int = 100
    default_variants_count: int = 2
    logo: Any = None
    pdf_font_size: int = 12
    pdf_margin_top: int = 15
    pdf_margin_bottom: int = 15


@dataclass(frozen=True)
class SaveSiteSettingsParams:
    school_name: str = ''
    teacher_name: str = ''
    default_subject: str = 'Физика'
    current_academic_year: str = '2025-2026'
    points_scale: int = 100
    default_variants_count: int = 2
    logo: Any = None
    clear_logo: bool = False
    pdf_font_size: int = 12
    pdf_margin_top: int = 15
    pdf_margin_bottom: int = 15


@dataclass(frozen=True)
class SaveSiteSettingsResult:
    status: str
