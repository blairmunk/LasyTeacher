import datetime as dt

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from core.models import AcademicYear
from curriculum.models import Course
from infrastructure.repositories.django_academic_year_activation_repo import (
    DjangoAcademicYearActivationRepository,
)
from infrastructure.repositories.django_academic_year_catalog_repo import (
    DjangoAcademicYearCatalogRepository,
)
from students.models import Student, StudentGroup


class DjangoAcademicYearRepositoryAdaptersTests(TestCase):
    def setUp(self):
        self.active_year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=dt.date(2026, 9, 1),
            end_date=dt.date(2027, 8, 31),
            is_active=True,
        )
        self.older_year = AcademicYear.objects.create(
            name='2025-2026',
            start_date=dt.date(2025, 9, 1),
            end_date=dt.date(2026, 8, 31),
        )
        self.catalog_repo = DjangoAcademicYearCatalogRepository()
        self.activation_repo = DjangoAcademicYearActivationRepository()

    def test_returns_clean_refs_in_display_order(self):
        years = self.catalog_repo.get_academic_years()
        active_year = self.catalog_repo.get_active_academic_year()
        older_year = self.catalog_repo.get_academic_year(
            str(self.older_year.pk),
        )

        self.assertEqual(
            [year.pk for year in years],
            [str(self.active_year.pk), str(self.older_year.pk)],
        )
        self.assertEqual(active_year.pk, str(self.active_year.pk))
        self.assertTrue(active_year.is_active)
        self.assertEqual(older_year.name, '2025-2026')

    def test_invalid_id_returns_none(self):
        self.assertIsNone(
            self.catalog_repo.get_academic_year('not-a-uuid')
        )

    def test_activation_switches_the_single_active_year(self):
        result = self.activation_repo.activate_academic_year(
            str(self.older_year.pk),
        )

        self.active_year.refresh_from_db()
        self.older_year.refresh_from_db()
        self.assertFalse(self.active_year.is_active)
        self.assertTrue(self.older_year.is_active)
        self.assertTrue(result.is_active)
        self.assertEqual(result.pk, str(self.older_year.pk))

    def test_activation_returns_none_for_invalid_id(self):
        self.assertIsNone(
            self.activation_repo.activate_academic_year('not-a-uuid')
        )

    def test_database_rejects_a_second_active_year(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            AcademicYear.objects.create(
                name='2027-2028',
                start_date=dt.date(2027, 9, 1),
                end_date=dt.date(2028, 8, 31),
                is_active=True,
            )


class AcademicYearRequestIntegrationTests(TestCase):
    def setUp(self):
        self.active_year = AcademicYear.objects.create(
            name='2026-2027',
            start_date=dt.date(2026, 9, 1),
            end_date=dt.date(2027, 8, 31),
            is_active=True,
        )
        self.older_year = AcademicYear.objects.create(
            name='2025-2026',
            start_date=dt.date(2025, 9, 1),
            end_date=dt.date(2026, 8, 31),
        )

    def test_requested_year_is_exposed_and_persisted_as_clean_ref(self):
        response = self.client.get(
            reverse('core:index'),
            {'year': str(self.older_year.pk)},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['current_year'].pk,
            str(self.older_year.pk),
        )
        self.assertEqual(
            self.client.session['academic_year_id'],
            str(self.older_year.pk),
        )
        self.assertEqual(
            [year.pk for year in response.context['all_years']],
            [str(self.active_year.pk), str(self.older_year.pk)],
        )

    def test_invalid_requested_year_repairs_session_with_active_year(self):
        session = self.client.session
        session['academic_year_id'] = str(self.older_year.pk)
        session.save()

        response = self.client.get(reverse('core:index'), {'year': 'bad-id'})

        self.assertEqual(
            response.context['current_year'].pk,
            str(self.active_year.pk),
        )
        self.assertEqual(
            self.client.session['academic_year_id'],
            str(self.active_year.pk),
        )

    def test_selected_year_filters_student_and_course_lists(self):
        older_student = Student.objects.create(
            last_name='Старший',
            first_name='Ученик',
        )
        active_student = Student.objects.create(
            last_name='Новый',
            first_name='Ученик',
        )
        older_group = StudentGroup.objects.create(
            name='8А',
            academic_year=self.older_year,
        )
        active_group = StudentGroup.objects.create(
            name='9А',
            academic_year=self.active_year,
        )
        older_group.students.add(older_student)
        active_group.students.add(active_student)
        older_course = Course.objects.create(
            name='Физика 8',
            subject='Физика',
            grade_level=8,
            year=self.older_year,
        )
        Course.objects.create(
            name='Физика 9',
            subject='Физика',
            grade_level=9,
            year=self.active_year,
        )

        student_response = self.client.get(
            reverse('students:list'),
            {'year': str(self.older_year.pk)},
        )
        course_response = self.client.get(reverse('curriculum:course-list'))

        self.assertEqual(
            [student.pk for student in student_response.context['students']],
            [str(older_student.pk)],
        )
        self.assertEqual(
            [course.pk for course in course_response.context['courses']],
            [str(older_course.pk)],
        )
