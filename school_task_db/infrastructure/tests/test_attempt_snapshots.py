import datetime as dt

from django.test import TestCase
from django.utils import timezone

from curriculum.models import Topic
from events.models import (
    AttemptSnapshot,
    Event,
    EventParticipation,
    Mark,
)
from infrastructure.repositories.django_attempt_snapshot_repo import (
    DjangoAttemptSnapshotRepository,
)
from infrastructure.tests.variant_task_factory import create_variant_task
from students.models import Student
from tasks.models import Task
from works.models import Variant, Work


class DjangoAttemptSnapshotRepositoryTests(TestCase):
    def setUp(self):
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.task = Task.objects.create(
            text='Найдите силу',
            answer='10 Н',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        work = Work.objects.create(name='Контрольная', work_type='test')
        variant = Variant.objects.create(
            work=work,
            number=3,
            work_name_snapshot='Контрольная по динамике',
        )
        self.variant_task = create_variant_task(
            variant=variant,
            task=self.task,
            order=1,
            max_points=2,
        )
        student = Student.objects.create(
            last_name='Иванов',
            first_name='Иван',
        )
        event = Event.objects.create(
            name='Контрольная 9А',
            work=work,
            planned_date=timezone.make_aware(
                dt.datetime(2026, 10, 15, 9, 0),
            ),
            status='reviewing',
        )
        participation = EventParticipation.objects.create(
            event=event,
            student=student,
            variant=variant,
            status='graded',
        )
        self.mark = Mark.objects.create(
            participation=participation,
            score=3,
            points=1,
            max_points=2,
            recommendations='Повторить второй закон Ньютона',
            checked_at=timezone.now(),
            checked_by='Учитель',
            task_scores={
                str(self.variant_task.pk): {
                    'task_id': str(self.task.pk),
                    'variant_task_id': str(self.variant_task.pk),
                    'points': 1,
                    'max_points': 2,
                    'comment': 'Ошибка в формуле',
                },
            },
        )

    def test_captures_versioned_attempt_and_task_results(self):
        repo = DjangoAttemptSnapshotRepository()

        first_ref = repo.capture_mark(str(self.mark.pk))
        self.mark.score = 4
        self.mark.recommendations = 'Проверить единицы измерения'
        self.mark.task_scores[str(self.variant_task.pk)]['points'] = 2
        self.mark.save()
        self.task.text = 'Изменённое задание банка'
        self.task.save(update_fields=['text'])
        second_ref = repo.capture_mark(str(self.mark.pk))

        first = AttemptSnapshot.objects.get(pk=first_ref.pk)
        second = AttemptSnapshot.objects.get(pk=second_ref.pk)
        first_task = first.task_results.get()
        second_task = second.task_results.get()
        self.assertEqual((first.revision, second.revision), (1, 2))
        self.assertEqual(first.score, 3)
        self.assertEqual(first.recommendations, 'Повторить второй закон Ньютона')
        self.assertEqual(first_task.points, 1)
        self.assertEqual(first_task.comment, 'Ошибка в формуле')
        self.assertEqual(second.score, 4)
        self.assertEqual(second.recommendations, 'Проверить единицы измерения')
        self.assertEqual(second_task.points, 2)
        self.assertEqual(
            second_task.variant_task.task_snapshot['text'],
            'Найдите силу',
        )
