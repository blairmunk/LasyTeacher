from io import StringIO

from django.core.management import call_command
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
        self.assertEqual(response.context['codifiers'][0].pk, str(self.codifier.pk))
        self.assertEqual(
            response.context['codifiers'][0].short_name,
            self.codifier.short_name,
        )
        self.assertEqual(response.context['codifiers'][0].content_entries_count, 2)
        self.assertEqual(response.context['codifiers'][0].requirements_count, 1)

    def test_codifier_detail_uses_clean_detail_context(self):
        response = self.client.get(
            reverse('codifier:spec-detail', args=[self.codifier.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['codifier'].pk, str(self.codifier.pk))
        self.assertEqual(response.context['codifier'].short_name, self.codifier.short_name)
        self.assertEqual(response.context['content_tree'][0].code, self.root.code)
        self.assertEqual(response.context['content_tree'][0].name, self.root.name)
        self.assertEqual(response.context['requirements'][0].code, self.requirement.code)
        self.assertEqual(response.context['requirements'][0].name, self.requirement.name)
        self.assertEqual(response.context['coverage'].total, 1)
        self.assertEqual(response.context['coverage'].covered, 1)

    def test_codifier_detail_returns_404_for_missing_codifier(self):
        response = self.client.get(
            reverse(
                'codifier:spec-detail',
                args=['550e8400-e29b-41d4-a716-446655440000'],
            )
        )

        self.assertEqual(response.status_code, 404)


class BuiltInCodifierImportCommandTests(TestCase):
    def test_imports_oge_and_ege_definitions(self):
        oge_output = StringIO()
        ege_output = StringIO()

        call_command('load_codifier_oge', stdout=oge_output)
        call_command('load_codifier_ege', stdout=ege_output)

        self.assertEqual(CodifierSpec.objects.count(), 2)
        self.assertEqual(
            ContentEntry.objects.filter(codifier__exam_type='oge').count(),
            61,
        )
        self.assertEqual(
            ContentEntry.objects.filter(codifier__exam_type='ege').count(),
            123,
        )
        self.assertEqual(
            Requirement.objects.filter(codifier__exam_type='oge').count(),
            11,
        )
        self.assertEqual(
            Requirement.objects.filter(codifier__exam_type='ege').count(),
            10,
        )
        self.assertIn('Кодификатор ОГЭ 2026 загружен', oge_output.getvalue())
        self.assertIn('Кодификатор ЕГЭ 2026 загружен', ege_output.getvalue())

    def test_reports_existing_codifier_without_duplicate_data(self):
        call_command('load_codifier_oge', stdout=StringIO())
        output = StringIO()

        call_command('load_codifier_oge', stdout=output)

        self.assertEqual(CodifierSpec.objects.count(), 1)
        self.assertEqual(ContentEntry.objects.count(), 61)
        self.assertIn('уже существует', output.getvalue())

    def test_clear_replaces_existing_codifier(self):
        call_command('load_codifier_oge', stdout=StringIO())
        original_pk = CodifierSpec.objects.get().pk
        output = StringIO()

        call_command('load_codifier_oge', '--clear', stdout=output)

        self.assertEqual(CodifierSpec.objects.count(), 1)
        self.assertNotEqual(CodifierSpec.objects.get().pk, original_pk)
        self.assertEqual(ContentEntry.objects.count(), 61)
        self.assertIn('Удалён кодификатор ОГЭ 2026', output.getvalue())

    def test_physics_topics_command_builds_catalog_and_bindings(self):
        call_command('load_codifier_oge', stdout=StringIO())
        call_command('load_codifier_ege', stdout=StringIO())
        output = StringIO()

        call_command('load_physics_topics', stdout=output)

        self.assertEqual(Topic.objects.filter(subject='Физика').count(), 31)
        self.assertEqual(
            sum(
                topic.subtopics.count()
                for topic in Topic.objects.filter(subject='Физика')
            ),
            113,
        )
        entry = ContentEntry.objects.get(
            codifier__short_name='ОГЭ 2026',
            code='1.3',
        )
        self.assertEqual(entry.topic.name, 'Механическое движение')
        self.assertEqual(entry.subtopic.name, 'Скорость')
        self.assertIn('Привязано: 159 элементов', output.getvalue())
        self.assertIn('Привязано 159/184', output.getvalue())

    def test_physics_topics_command_reports_missing_codifiers(self):
        output = StringIO()

        call_command('load_physics_topics', stdout=output)

        self.assertEqual(Topic.objects.count(), 31)
        self.assertEqual(ContentEntry.objects.count(), 0)
        self.assertIn('Проблемы:', output.getvalue())
        self.assertIn('ОГЭ 2026 1.1 — не найден', output.getvalue())
