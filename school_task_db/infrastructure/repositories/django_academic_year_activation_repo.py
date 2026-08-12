"""Django command adapter for academic year activation."""

from django.core.exceptions import ValidationError
from django.db import transaction

from core.models import AcademicYear
from core_logic.entities.academic_year import AcademicYearRef
from core_logic.interfaces.academic_year_activation_repo import (
    IAcademicYearActivationRepository,
)
from infrastructure.repositories.django_academic_year_support import (
    academic_year_to_ref,
)


class DjangoAcademicYearActivationRepository(
    IAcademicYearActivationRepository,
):
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
        return academic_year_to_ref(year)
