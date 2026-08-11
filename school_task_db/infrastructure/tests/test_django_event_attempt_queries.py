from django.test import TestCase
from django.utils import timezone

from events.models import AttemptSnapshot, Event, EventParticipation, Mark
from infrastructure.repositories.django_attempt_snapshot_repo import (
    DjangoAttemptSnapshotRepository,
)
from infrastructure.repositories.django_event_attempt_repo import (
    DjangoEventAttemptRepository,
)
from students.models import Student
from works.models import Variant, Work


class DjangoEventAttemptQueryTests(TestCase):
    def setUp(self):
        self.student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        self.work = Work.objects.create(name='Контрольная')
        self.variant = Variant.objects.create(
            work=self.work,
            number=1,
            work_name_snapshot=self.work.name,
        )
        self.event = Event.objects.create(
            name='КР 9Б',
            work=self.work,
            planned_date=timezone.now(),
            status='graded',
        )
        self.participation = EventParticipation.objects.create(
            event=self.event,
            student=self.student,
            variant=self.variant,
            status='graded',
        )
        self.mark = Mark.objects.create(
            participation=self.participation,
            score=2,
            points=5,
            max_points=7,
            task_scores={
                'task-1': {'points': 0, 'max_points': 2},
            },
        )
        first_ref = DjangoAttemptSnapshotRepository().capture_mark(
            str(self.mark.pk),
        )
        self.first_attempt = AttemptSnapshot.objects.get(pk=first_ref.pk)

    def test_remedial_queries_ignore_uncaptured_mark_edits(self):
        original_task_scores = dict(self.first_attempt.task_scores_snapshot)
        self.mark.score = 5
        self.mark.points = 7
        self.mark.task_scores = {}
        self.mark.save(update_fields=['score', 'points', 'task_scores'])

        attempt_ref, participation_result = self._read_attempt()

        self.assertEqual(
            attempt_ref.attempt_snapshot_id,
            str(self.first_attempt.pk),
        )
        self.assertEqual(attempt_ref.score, 2)
        self.assertEqual(participation_result.score, 2)
        self.assertEqual(participation_result.points, 5)
        self.assertEqual(participation_result.task_scores, original_task_scores)

    def test_remedial_preview_uses_captured_variant(self):
        replacement_variant = Variant.objects.create(
            work=self.work,
            number=2,
            work_name_snapshot=self.work.name,
        )
        self.participation.variant = replacement_variant
        self.participation.save(update_fields=['variant'])

        _attempt_ref, participation_result = self._read_attempt()

        self.assertEqual(participation_result.variant.pk, str(self.variant.pk))
        self.assertEqual(participation_result.variant.number, 1)

    def test_remedial_queries_select_latest_captured_revision(self):
        self.mark.score = 5
        self.mark.points = 7
        self.mark.task_scores = {}
        self.mark.save(update_fields=['score', 'points', 'task_scores'])
        second_ref = DjangoAttemptSnapshotRepository().capture_mark(
            str(self.mark.pk),
        )
        self.mark.score = 3
        self.mark.save(update_fields=['score'])

        attempt_ref, participation_result = self._read_attempt()

        self.assertEqual(attempt_ref.attempt_snapshot_id, second_ref.pk)
        self.assertEqual(attempt_ref.score, 5)
        self.assertEqual(participation_result.score, 5)
        self.assertEqual(participation_result.points, 7)
        self.assertEqual(participation_result.task_scores, {})

    def test_unchecked_participation_has_no_captured_attempt(self):
        second_student = Student.objects.create(
            last_name='Сидоров',
            first_name='Сидор',
        )
        EventParticipation.objects.create(
            event=self.event,
            student=second_student,
            status='assigned',
        )
        repo = DjangoEventAttemptRepository()

        attempt_ref = repo.get_latest_student_attempt(
            str(self.event.pk),
            str(second_student.pk),
        )
        rows = repo.get_participation_attempts(str(self.event.pk))
        unchecked_row = next(
            row for row in rows if row.student.pk == str(second_student.pk)
        )

        self.assertIsNone(attempt_ref)
        self.assertIsNone(unchecked_row.score)
        self.assertEqual(unchecked_row.task_scores, {})

    def _read_attempt(self):
        repo = DjangoEventAttemptRepository()
        return (
            repo.get_latest_student_attempt(
                str(self.event.pk),
                str(self.student.pk),
            ),
            repo.get_participation_attempts(str(self.event.pk))[0],
        )
