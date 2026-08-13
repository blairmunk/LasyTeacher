from django.test import TestCase

from codifier.models import CodifierSpec, ContentEntry, Requirement
from curriculum.models import Topic
from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
from tasks.models import Task


class TaskContentSnapshotClassificationTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        self.task = Task.objects.create(
            text='Найти силу',
            answer='10 Н',
            topic=self.topic,
            content_element='1.2',
            task_type='computational',
            difficulty=2,
        )
        oge = CodifierSpec.objects.create(
            name='ОГЭ по физике 2026',
            short_name='ОГЭ 2026',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        ege = CodifierSpec.objects.create(
            name='ЕГЭ по физике 2026',
            short_name='ЕГЭ 2026',
            subject='Физика',
            exam_type='ege',
            year=2026,
        )
        self.oge_entry = ContentEntry.objects.create(
            codifier=oge,
            code='1.2',
            name='ОГЭ: механическое движение',
            topic=self.topic,
        )
        self.ege_entry = ContentEntry.objects.create(
            codifier=ege,
            code='1.2',
            name='ЕГЭ: динамика',
            topic=self.topic,
        )
        self.requirement = Requirement.objects.create(
            codifier=ege,
            code='2.1',
            name='Решать задачи',
        )

    def test_explicit_entries_take_precedence_over_legacy_code_matching(self):
        self.ege_entry.tasks.add(self.task)

        snapshot = build_task_content_snapshots([self.task])[str(self.task.pk)]

        self.assertEqual(
            snapshot.content_element_descriptions,
            ('ЕГЭ 2026: ЕГЭ: динамика',),
        )
        self.assertEqual(snapshot.codifier_content_entries[0].code, '1.2')
        self.assertEqual(
            snapshot.codifier_content_entries[0].codifier_short_name,
            'ЕГЭ 2026',
        )
        self.assertEqual(snapshot.content_element, '')

    def test_explicit_requirements_suppress_legacy_requirement_code(self):
        self.task.requirement_element = '2.1'
        self.task.save(update_fields=['requirement_element'])
        self.requirement.tasks.add(self.task)

        snapshot = build_task_content_snapshots([self.task])[str(self.task.pk)]

        self.assertEqual(snapshot.requirement_element, '')
        self.assertEqual(snapshot.codifier_requirements[0].code, '2.1')

    def test_legacy_code_matching_remains_when_explicit_entries_are_empty(self):
        snapshot = build_task_content_snapshots([self.task])[str(self.task.pk)]

        self.assertEqual(
            set(snapshot.content_element_descriptions),
            {
                'ОГЭ 2026: ОГЭ: механическое движение',
                'ЕГЭ 2026: ЕГЭ: динамика',
            },
        )
        self.assertEqual(snapshot.content_element, '1.2')
