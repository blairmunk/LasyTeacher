import datetime as dt
from unittest import TestCase

from core_logic.entities.academic_year import AcademicYearRef
from core_logic.interfaces.academic_year_activation_repo import (
    IAcademicYearActivationRepository,
)
from core_logic.interfaces.academic_year_catalog_repo import (
    IAcademicYearCatalogRepository,
)
from core_logic.use_cases.get_academic_year_list import (
    GetAcademicYearListUseCase,
)
from core_logic.use_cases.activate_academic_year import (
    ActivateAcademicYearRequest,
    ActivateAcademicYearUseCase,
)
from core_logic.use_cases.resolve_academic_year import (
    ResolveAcademicYearRequest,
    ResolveAcademicYearUseCase,
)


class FakeAcademicYearRepository(
    IAcademicYearCatalogRepository,
    IAcademicYearActivationRepository,
):
    def __init__(self, years, active_year=None):
        self.years = years
        self.active_year = active_year

    def get_academic_year(self, year_id):
        return next((year for year in self.years if year.pk == year_id), None)

    def get_active_academic_year(self):
        return self.active_year

    def get_academic_years(self):
        return self.years

    def activate_academic_year(self, year_id):
        year = self.get_academic_year(year_id)
        self.active_year = year
        return year


class AcademicYearSelectionTests(TestCase):
    def setUp(self):
        self.active_year = _year('active', '2026-2027', is_active=True)
        self.selected_year = _year('selected', '2025-2026')
        self.repo = FakeAcademicYearRepository(
            [self.active_year, self.selected_year],
            active_year=self.active_year,
        )
        self.use_case = ResolveAcademicYearUseCase(self.repo)

    def test_requested_year_has_priority_over_stored_year(self):
        result = self.use_case.execute(
            ResolveAcademicYearRequest(
                requested_year_id=self.selected_year.pk,
                stored_year_id=self.active_year.pk,
            )
        )

        self.assertEqual(result.current_year, self.selected_year)
        self.assertEqual(result.year_id, self.selected_year.pk)

    def test_stored_year_is_used_without_request_override(self):
        result = self.use_case.execute(
            ResolveAcademicYearRequest(stored_year_id=self.selected_year.pk),
        )

        self.assertEqual(result.current_year, self.selected_year)

    def test_invalid_selection_falls_back_to_active_year(self):
        result = self.use_case.execute(
            ResolveAcademicYearRequest(requested_year_id='missing'),
        )

        self.assertEqual(result.current_year, self.active_year)

    def test_empty_repository_returns_empty_selection_and_list(self):
        repo = FakeAcademicYearRepository([])

        selection = ResolveAcademicYearUseCase(repo).execute(
            ResolveAcademicYearRequest(),
        )
        years = GetAcademicYearListUseCase(repo).execute()

        self.assertIsNone(selection.current_year)
        self.assertEqual(selection.year_id, '')
        self.assertEqual(years.academic_years, ())

    def test_academic_year_list_copies_repository_collection(self):
        result = GetAcademicYearListUseCase(self.repo).execute()

        self.repo.years.clear()

        self.assertEqual(
            result.academic_years,
            (self.active_year, self.selected_year),
        )

    def test_activate_academic_year_delegates_to_repository(self):
        result = ActivateAcademicYearUseCase(self.repo).execute(
            ActivateAcademicYearRequest(year_id=self.selected_year.pk),
        )

        self.assertEqual(result, self.selected_year)
        self.assertEqual(self.repo.active_year, self.selected_year)


def _year(year_id, name, is_active=False):
    return AcademicYearRef(
        pk=year_id,
        name=name,
        start_date=dt.date(2026, 9, 1),
        end_date=dt.date(2027, 8, 31),
        is_active=is_active,
    )
