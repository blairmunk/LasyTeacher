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

    def test_global_search_returns_text_results_from_clean_use_case(self):
        topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        task = Task.objects.create(
            text='Задача про скорость',
            answer='Ответ',
            topic=topic,
            task_type='computational',
            difficulty=2,
        )
        work = Work.objects.create(name='Контрольная скорость')
        group = AnalogGroup.objects.create(name='скорость')

        response = self.client.get(reverse('core:search'), {'q': 'скорость'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], 'скорость')
        self.assertEqual(response.context['search_mode'], 'text')
        self.assertEqual(response.context['total_found'], 3)
        self.assertEqual(list(response.context['results']['tasks']), [task])
        self.assertEqual(list(response.context['results']['works']), [work])
        self.assertEqual(list(response.context['results']['groups']), [group])
        self.assertEqual(response.context['found_text'], '3 результата')

    def test_global_search_empty_query_returns_empty_context(self):
        response = self.client.get(reverse('core:search'), {'q': '  '})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['query'], '')
        self.assertEqual(response.context['results'], {})
        self.assertEqual(response.context['total_found'], 0)
        self.assertIsNone(response.context['search_mode'])
        self.assertEqual(response.context['found_text'], '')
