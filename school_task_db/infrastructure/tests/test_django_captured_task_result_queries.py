from django.test import TestCase
from django.utils import timezone

from core_logic.value_objects.task_content_snapshot import TaskContentSnapshot
from events.models import (
    AttemptSnapshot,
    AttemptTaskSnapshot,
    Event,
    EventParticipation,
    Mark,
)
from infrastructure.services.django_captured_task_result_queries import (
    latest_assessable_task_results,
)
from students.models import Student
from works.models import Work


class DjangoCapturedTaskResultQueryTests(TestCase):
    def setUp(self):
        student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        work = Work.objects.create(name='Контрольная')
        event = Event.objects.create(
            name='Контрольная 8А',
            work=work,
            planned_date=timezone.now(),
        )
        self.participation = EventParticipation.objects.create(
            event=event,
            student=student,
        )
        self.mark = Mark.objects.create(participation=self.participation)

    def test_returns_only_valid_assessable_results_from_latest_revision(self):
        old_attempt = self._attempt(revision=1)
        latest_attempt = self._attempt(revision=2)
        self._task_result(
            old_attempt,
            task_id='old-task',
            text='Старая ревизия',
            points=2,
        )
        selected = self._task_result(
            latest_attempt,
            task_id='task-1',
            text='Зафиксированное условие',
            points=None,
            expected_max_points=3,
            checked_max_points=5,
            comment='Проверьте формулу',
        )
        self._task_result(
            latest_attempt,
            task_id='demo-task',
            text='Демонстрационное задание',
            is_assessable=False,
        )
        AttemptTaskSnapshot.objects.create(
            attempt=latest_attempt,
            task_id_snapshot='broken-task',
            task_content_snapshot={},
            order_snapshot=3,
            is_assessable_snapshot=True,
            expected_max_points_snapshot=2,
        )

        results = latest_assessable_task_results(
            (self.participation.pk,),
        )

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.task.task_id, selected.task_id_snapshot)
        self.assertEqual(result.task.text, 'Зафиксированное условие')
        self.assertEqual(result.points, 0)
        self.assertEqual(result.max_points, 5)
        self.assertEqual(result.comment, 'Проверьте формулу')
        self.assertEqual(result.student_id, str(self.participation.student_id))
        self.assertEqual(result.event_id, str(self.participation.event_id))

    def _attempt(self, revision):
        participation = self.participation
        return AttemptSnapshot.objects.create(
            participation=participation,
            mark=self.mark,
            revision=revision,
            student_id_snapshot=str(participation.student_id),
            student_name_snapshot=participation.student.get_full_name(),
            event_id_snapshot=str(participation.event_id),
            event_name_snapshot=participation.event.name,
            event_date_snapshot=participation.event.planned_date,
            work_id_snapshot=str(participation.event.work_id),
            work_name_snapshot=participation.event.work.name,
        )

    @staticmethod
    def _task_result(
        attempt,
        task_id,
        text,
        points=1,
        expected_max_points=2,
        checked_max_points=None,
        comment='',
        is_assessable=True,
    ):
        task_snapshot = TaskContentSnapshot(
            task_id=task_id,
            text=text,
            answer='',
            topic_name='Динамика',
        )
        return AttemptTaskSnapshot.objects.create(
            attempt=attempt,
            task_id_snapshot=task_id,
            task_content_snapshot=task_snapshot.to_mapping(),
            order_snapshot=attempt.task_results.count() + 1,
            is_assessable_snapshot=is_assessable,
            expected_max_points_snapshot=expected_max_points,
            points=points,
            checked_max_points=checked_max_points,
            comment=comment,
        )
