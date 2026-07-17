from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from curriculum.models import Topic
from events.models import Event
from students.models import Student
from task_groups.models import AnalogGroup
from tasks.models import Task
from works.models import Variant, Work


class CoreViewsTests(TestCase):
    def test_index_uses_clean_dashboard_summary_context(self):
        topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        work = Work.objects.create(name='Контрольная')
        Variant.objects.create(
            work=work,
            number=1,
            work_name_snapshot=work.name,
        )
        Variant.objects.create(
            work=None,
            number=2,
            work_name_snapshot='Сирота',
        )
        Student.objects.create(last_name='Иванов', first_name='Иван')
        Event.objects.create(name='КР', work=work, planned_date=timezone.now())
        AnalogGroup.objects.create(name='Скорость')

        response = self.client.get(reverse('core:index'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['tasks_count'], 1)
        self.assertEqual(response.context['works_count'], 1)
        self.assertEqual(response.context['variants_count'], 2)
        self.assertEqual(response.context['orphan_variants_count'], 1)
        self.assertEqual(response.context['students_count'], 1)
        self.assertEqual(response.context['events_count'], 1)
        self.assertEqual(response.context['groups_count'], 1)
