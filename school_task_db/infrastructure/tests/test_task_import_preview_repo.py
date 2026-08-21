from django.test import TestCase

from codifier.models import CodifierSpec, ContentEntry
from core_logic.entities.task_import import (
    TaskImportClassificationKey,
    TaskImportPreviewLookup,
)
from curriculum.models import SubTopic, Topic
from infrastructure.repositories.django_task_import_preview_repo import (
    DjangoTaskImportPreviewRepository,
)
from task_groups.models import AnalogGroup
from tasks.models import Task


class DjangoTaskImportPreviewRepositoryTests(TestCase):
    def test_returns_only_requested_existing_facts(self):
        topic = Topic.objects.create(
            name='Динамика',
            subject='Физика',
            section='Механика',
            grade_level=9,
        )
        subtopic = SubTopic.objects.create(topic=topic, name='Силы')
        group = AnalogGroup.objects.create(name='Силы')
        task = Task.objects.create(
            text='Найдите силу',
            topic=topic,
            subtopic=subtopic,
            difficulty=2,
            task_type='computational',
        )
        codifier = CodifierSpec.objects.create(
            name='ОГЭ по физике 2026',
            short_name='ОГЭ 2026',
            subject='Физика',
            exam_type='oge',
            year=2026,
        )
        ContentEntry.objects.create(
            codifier=codifier,
            code='1.1',
            name='Механика',
        )
        classification = TaskImportClassificationKey(
            kind='content',
            subject='Физика',
            exam_type='oge',
            year=2026,
            code='1.1',
        )
        missing_classification = TaskImportClassificationKey(
            kind='requirement',
            subject='Физика',
            exam_type='oge',
            year=2026,
            code='9.9',
        )

        facts = DjangoTaskImportPreviewRepository().get_facts(
            TaskImportPreviewLookup(
                task_ids=(str(task.pk),),
                group_ids=(str(group.pk),),
                topic_ids=(str(topic.pk),),
                subtopic_ids=(str(subtopic.pk),),
                classifications=(classification, missing_classification),
            ),
        )

        self.assertEqual(facts.existing_task_ids, {str(task.pk)})
        self.assertEqual(facts.existing_group_ids, {str(group.pk)})
        self.assertEqual(facts.existing_topic_ids, {str(topic.pk)})
        self.assertEqual(
            facts.subtopic_topic_ids,
            {str(subtopic.pk): str(topic.pk)},
        )
        self.assertEqual(
            facts.existing_classifications,
            {classification},
        )
