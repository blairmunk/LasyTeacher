from django.test import TestCase
from django.utils import timezone

from curriculum.models import Course
from events.models import Event, EventParticipation, Mark
from infrastructure.repositories.django_journal_catalog_repo import (
    DjangoJournalCatalogRepository,
)
from infrastructure.repositories.django_journal_report_repo import (
    DjangoJournalReportRepository,
)
from infrastructure.tests.variant_task_factory import capture_attempt_snapshot
from students.models import Student, StudentGroup
from works.models import Variant, Work


class DjangoJournalRepositoryTests(TestCase):
    def test_returns_course_group_links(self):
        student = Student.objects.create(last_name='Иванов', first_name='Иван')
        group = StudentGroup.objects.create(name='7А')
        group.students.add(student)
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )
        course.student_groups.add(group)
        work = Work.objects.create(name='Контрольная')
        event = Event.objects.create(
            name='КР',
            work=work,
            course=course,
            status='planned',
            planned_date=timezone.now(),
        )
        EventParticipation.objects.create(
            event=event,
            student=student,
            status='assigned',
        )

        data = DjangoJournalCatalogRepository().get_journal_select(year=None)

        self.assertEqual(data.groups[0].pk, str(group.pk))
        self.assertEqual(data.groups[0].name, group.name)
        self.assertEqual(data.courses[0].pk, str(course.pk))
        self.assertEqual(data.courses[0].name, course.name)
        self.assertEqual(data.journal_links[0]['course'].pk, str(course.pk))
        self.assertEqual(data.journal_links[0]['group'].pk, str(group.pk))
        self.assertEqual(data.journal_links[0]['group'].students_count, 1)
        self.assertEqual(data.journal_links[0]['event_count'], 1)
        self.assertEqual(data.active_report, 'journal')

    def test_returns_snapshot_grades_and_variants(self):
        work = Work.objects.create(name='Контрольная')
        course = Course.objects.create(
            name='Физика 7',
            subject='Физика',
            grade_level=7,
            is_active=True,
        )
        graded_student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        missing_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        group = StudentGroup.objects.create(name='7А')
        group.students.add(graded_student, missing_student)
        event = Event.objects.create(
            name='КР',
            work=work,
            course=course,
            status='graded',
            planned_date=timezone.now(),
        )
        captured_variant = Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
        )
        participation = EventParticipation.objects.create(
            event=event,
            student=graded_student,
            variant=captured_variant,
            status='graded',
        )
        mark = Mark.objects.create(
            participation=participation,
            score=4,
            points=8,
            max_points=10,
        )
        capture_attempt_snapshot(mark)
        mark.score = 2
        mark.points = 1
        mark.save(update_fields=['score', 'points'])
        replacement_variant = Variant.objects.create(
            work=work,
            number=2,
            work_name_snapshot='Изменённая работа',
        )
        participation.variant = replacement_variant
        participation.status = 'absent'
        participation.save(update_fields=['variant', 'status'])

        data = DjangoJournalReportRepository().get_journal_source(
            course_id=course.pk,
            group_id=group.pk,
            year=None,
        )

        self.assertEqual(data.course.pk, str(course.pk))
        self.assertEqual(data.group.pk, str(group.pk))
        self.assertEqual(data.events[0].pk, str(event.pk))
        self.assertEqual(data.events[0].work.pk, str(work.pk))
        self.assertEqual(len(data.students), 2)
        self.assertEqual(len(data.entries), 1)
        entry = data.entries[0]
        self.assertEqual(entry.student_id, str(graded_student.pk))
        self.assertEqual(entry.participation.status, 'graded')
        self.assertEqual(entry.mark.score, 4)
        self.assertEqual(entry.mark.points, 8)
        self.assertEqual(entry.variant.pk, str(captured_variant.pk))
        self.assertEqual(entry.variant.number, 1)
        self.assertEqual(entry.variant.work_name_snapshot, work.name)
