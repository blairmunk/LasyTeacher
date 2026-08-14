"""Django read adapter for academic years."""

from django.core.exceptions import ValidationError

from core.models import AcademicYear
from core_logic.entities.academic_year import AcademicYearRef
from core_logic.interfaces.academic_year_catalog_repo import (
    IAcademicYearCatalogRepository,
)
from infrastructure.repositories.django_academic_year_support import (
    academic_year_to_ref,
)


class DjangoAcademicYearCatalogRepository(IAcademicYearCatalogRepository):
    def get_academic_year(self, year_id: str) -> AcademicYearRef | None:
        if not year_id:
            return None
        try:
            year = AcademicYear.objects.filter(pk=year_id).first()
        except (ValidationError, ValueError):
            return None
        return academic_year_to_ref(year) if year else None

    def get_active_academic_year(self) -> AcademicYearRef | None:
        year = AcademicYear.objects.filter(is_active=True).first()
        return academic_year_to_ref(year) if year else None

    def get_academic_years(self) -> tuple[AcademicYearRef, ...]:
        return tuple(
            academic_year_to_ref(year)
            for year in AcademicYear.objects.all().order_by('-start_date')
        )
