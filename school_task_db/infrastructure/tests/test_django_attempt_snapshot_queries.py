from django.test import TestCase
from django.utils import timezone

from events.models import (
    AttemptSnapshot,
    AttemptTaskSnapshot,
    Event,
    EventParticipation,
    Mark,
)
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from students.models import Student
from works.models import Work


class DjangoAttemptSnapshotQueryTests(TestCase):
    def setUp(self):
        work = Work.objects.create(name='Контрольная')
        event = Event.objects.create(
            name='Контрольная 8А',
            work=work,
            planned_date=timezone.now(),
        )
        first_student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        second_student = Student.objects.create(
            last_name='Петров',
            first_name='Пётр',
        )
        self.first_participation = EventParticipation.objects.create(
            event=event,
            student=first_student,
        )
        self.second_participation = EventParticipation.objects.create(
            event=event,
            student=second_student,
        )
        self.first_mark = Mark.objects.create(
            participation=self.first_participation,
        )
        self.second_mark = Mark.objects.create(
            participation=self.second_participation,
        )

    def test_returns_latest_revision_with_ordered_task_results(self):
        old_attempt = self._attempt(self.first_mark, revision=1, score=2)
        latest_attempt = self._attempt(self.first_mark, revision=2, score=4)
        second_attempt = self._attempt(self.second_mark, revision=1, score=3)
        self._task_result(old_attempt, order=1, task_id='old-task')
        second_result = self._task_result(
            latest_attempt,
            order=2,
            task_id='task-2',
        )
        first_result = self._task_result(
            latest_attempt,
            order=1,
            task_id='task-1',
        )

        with self.assertNumQueries(2):
            attempts = latest_attempts_by_participation(
                (
                    self.first_participation.pk,
                    self.second_participation.pk,
                ),
            )

        self.assertEqual(
            attempts[self.first_participation.pk].pk,
            latest_attempt.pk,
        )
        self.assertEqual(
            attempts[self.second_participation.pk].pk,
            second_attempt.pk,
        )
        self.assertEqual(
            [
                result.pk
                for result in attempts[
                    self.first_participation.pk
                ].captured_task_results
            ],
            [first_result.pk, second_result.pk],
        )

    def test_can_skip_task_result_prefetch(self):
        latest_attempt = self._attempt(self.first_mark, revision=1, score=4)
        self._task_result(latest_attempt, order=1, task_id='task-1')

        with self.assertNumQueries(1):
            attempts = latest_attempts_by_participation(
                (self.first_participation.pk,),
                include_task_results=False,
            )

        attempt = attempts[self.first_participation.pk]
        self.assertEqual(attempt.pk, latest_attempt.pk)
        self.assertFalse(hasattr(attempt, 'captured_task_results'))

    def test_empty_input_performs_no_queries(self):
        with self.assertNumQueries(0):
            attempts = latest_attempts_by_participation(iter(()))

        self.assertEqual(attempts, {})

    def _attempt(self, mark, revision, score):
        participation = mark.participation
        return AttemptSnapshot.objects.create(
            participation=participation,
            mark=mark,
            revision=revision,
            student_id_snapshot=str(participation.student_id),
            student_name_snapshot=participation.student.get_full_name(),
            event_id_snapshot=str(participation.event_id),
            event_name_snapshot=participation.event.name,
            event_date_snapshot=participation.event.planned_date,
            work_id_snapshot=str(participation.event.work_id),
            work_name_snapshot=participation.event.work.name,
            score=score,
        )

    @staticmethod
    def _task_result(attempt, order, task_id):
        return AttemptTaskSnapshot.objects.create(
            attempt=attempt,
            task_id_snapshot=task_id,
            task_content_snapshot={},
            order_snapshot=order,
            is_assessable_snapshot=True,
            expected_max_points_snapshot=2,
        )
