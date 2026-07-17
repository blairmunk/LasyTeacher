from django.test import TestCase
from django.urls import reverse

from codifier.models import CodifierSpec, ContentEntry, Requirement
from curriculum.models import Topic
from tasks.models import Task


class CodifierViewsTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.task = Task.objects.create(
            text='Задача',
            answer='Ответ',
            topic=self.topic,
            task_type='computational',
            difficulty=2,
        )
        self.codifier = CodifierSpec.objects.create(
            name='ОГЭ 2026 Физика',
            short_name='ОГЭ 2026',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        self.root = ContentEntry.objects.create(
            codifier=self.codifier,
            code='1',
            name='Механика',
        )
        self.leaf = ContentEntry.objects.create(
            codifier=self.codifier,
            parent=self.root,
            code='1.1',
            name='Кинематика',
            topic=self.topic,
        )
        self.requirement = Requirement.objects.create(
            codifier=self.codifier,
            code='1',
            name='Знать понятия',
        )

    def test_codifier_list_uses_clean_list_context(self):
        response = self.client.get(reverse('codifier:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['codifiers']), [self.codifier])

    def test_codifier_detail_uses_clean_detail_context(self):
        response = self.client.get(
            reverse('codifier:spec-detail', args=[self.codifier.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['codifier'], self.codifier)
        self.assertEqual(response.context['content_tree'], [self.root])
        self.assertEqual(list(response.context['requirements']), [self.requirement])
        self.assertEqual(response.context['coverage']['total'], 1)
        self.assertEqual(response.context['coverage']['covered'], 1)

    def test_codifier_detail_returns_404_for_missing_codifier(self):
        response = self.client.get(
            reverse(
                'codifier:spec-detail',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)
