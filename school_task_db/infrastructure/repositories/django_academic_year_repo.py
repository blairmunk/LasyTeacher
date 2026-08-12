"""Django implementation of the academic year repository."""

from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import AcademicYear
from core_logic.entities.academic_year import AcademicYearRef
from core_logic.interfaces.academic_year_activation_repo import (
    IAcademicYearActivationRepository,
)
from core_logic.interfaces.academic_year_catalog_repo import (
    IAcademicYearCatalogRepository,
)


class DjangoAcademicYearRepository(
    IAcademicYearCatalogRepository,
    IAcademicYearActivationRepository,
):
    def get_academic_year(self, year_id: str) -> AcademicYearRef | None:
        if not year_id:
            return None
        try:
            year = AcademicYear.objects.filter(pk=year_id).first()
        except (ValidationError, ValueError):
            return None
        return self._to_ref(year) if year else None

    def get_active_academic_year(self) -> AcademicYearRef | None:
        year = AcademicYear.objects.filter(is_active=True).first()
        return self._to_ref(year) if year else None

    def get_academic_years(self) -> list[AcademicYearRef]:
        return [
            self._to_ref(year)
            for year in AcademicYear.objects.all().order_by('-start_date')
        ]

    @transaction.atomic
    def activate_academic_year(
        self,
        year_id: str,
    ) -> AcademicYearRef | None:
        try:
            year = AcademicYear.objects.select_for_update().filter(
                pk=year_id,
            ).first()
        except (ValidationError, ValueError):
            return None
        if year is None:
            return None

        list(
            AcademicYear.objects.select_for_update()
            .filter(is_active=True)
            .values_list('pk', flat=True)
        )
        AcademicYear.objects.filter(is_active=True).exclude(
            pk=year.pk,
        ).update(is_active=False)
        if not year.is_active:
            AcademicYear.objects.filter(pk=year.pk).update(is_active=True)
            year.is_active = True
        return self._to_ref(year)

    @staticmethod
    def _to_ref(year: AcademicYear) -> AcademicYearRef:
        return AcademicYearRef(
            pk=str(year.pk),
            name=year.name,
            start_date=year.start_date,
            end_date=year.end_date,
            is_active=year.is_active,
        )
