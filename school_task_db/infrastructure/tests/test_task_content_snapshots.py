from django.test import TestCase

from codifier.models import CodifierSpec, ContentEntry, Requirement
from curriculum.models import Topic
from infrastructure.services.task_content_snapshots import (
    build_task_content_snapshots,
)
from tasks.models import ImageAsset, Task, TaskImage


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

    def test_snapshot_contains_explicit_content_entries(self):
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

    def test_snapshot_contains_explicit_requirements(self):
        self.requirement.tasks.add(self.task)

        snapshot = build_task_content_snapshots([self.task])[str(self.task.pk)]

        self.assertEqual(snapshot.requirement_element, '')
        self.assertEqual(snapshot.codifier_requirements[0].code, '2.1')

    def test_snapshot_does_not_infer_classification_without_relations(self):
        snapshot = build_task_content_snapshots([self.task])[str(self.task.pk)]

        self.assertEqual(snapshot.content_element_descriptions, ())
        self.assertEqual(snapshot.codifier_content_entries, ())
        self.assertEqual(snapshot.content_element, '')

    def test_snapshot_references_immutable_image_asset_by_uuid(self):
        asset = ImageAsset.objects.create(
            file='image_assets/ab/asset.png',
            checksum='a' * 64,
            byte_size=10,
            mime_type='image/png',
            original_filename='diagram.png',
        )
        task_image = TaskImage.objects.create(
            task=self.task,
            asset=asset,
            position='bottom_70',
            caption='Схема',
        )

        snapshot = build_task_content_snapshots([self.task])[str(self.task.pk)]

        self.assertEqual(snapshot.images[0].image_id, str(task_image.pk))
        self.assertEqual(snapshot.images[0].asset_id, str(asset.pk))
        self.assertEqual(snapshot.images[0].file_name, asset.file.name)
