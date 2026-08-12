"""Shared mapping helpers for Django academic year adapters."""

from core.models import AcademicYear
from core_logic.entities.academic_year import AcademicYearRef


def academic_year_to_ref(year: AcademicYear) -> AcademicYearRef:
    return AcademicYearRef(
        pk=str(year.pk),
        name=year.name,
        start_date=year.start_date,
        end_date=year.end_date,
        is_active=year.is_active,
    )
