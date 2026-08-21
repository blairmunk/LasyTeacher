from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportClassificationKey,
    TaskImportPreviewFacts,
)
from core_logic.services.task_import_preview_service import (
    TaskImportPreviewService,
)


class TaskImportPreviewServiceTests(TestCase):
    TASK_ID = '550e8400-e29b-41d4-a716-446655440001'
    GROUP_ID = '770e8400-e29b-41d4-a716-446655440001'
    TOPIC_ID = '660e8400-e29b-41d4-a716-446655440001'
    SUBTOPIC_ID = '661e8400-e29b-41d4-a716-446655440001'
    CLASSIFICATION = TaskImportClassificationKey(
        kind='content',
        subject='Физика',
        exam_type='oge',
        year=2026,
        code='1.1',
    )

    def setUp(self):
        self.service = TaskImportPreviewService()

    def test_builds_deduplicated_database_lookup(self):
        lookup = self.service.build_lookup(self._payload())

        self.assertEqual(lookup.task_ids, (self.TASK_ID,))
        self.assertEqual(lookup.group_ids, (self.GROUP_ID,))
        self.assertEqual(lookup.topic_ids, (self.TOPIC_ID,))
        self.assertEqual(lookup.subtopic_ids, (self.SUBTOPIC_ID,))
        self.assertEqual(lookup.classifications, (self.CLASSIFICATION,))

    def test_declared_dependencies_are_not_reported_as_missing(self):
        preview = self.service.build(
            self._payload(),
            TaskImportPreviewFacts(),
        )

        self.assertEqual(
            preview['task_uuid_counts'],
            {'existing': 0, 'new': 1, 'invalid': 0},
        )
        self.assertEqual(
            preview['group_uuid_counts'],
            {'existing': 0, 'new': 1, 'invalid': 0},
        )
        self.assertEqual(
            preview['dependency_counts'],
            {
                'missing_topics': 0,
                'missing_subtopics': 0,
                'missing_groups': 0,
                'broken_references': 0,
                'missing_classifications': 1,
            },
        )

    def test_uses_database_facts_for_external_references(self):
        payload = self._payload()
        payload['topics'] = []
        payload['analog_groups'] = []
        facts = TaskImportPreviewFacts(
            existing_task_ids={self.TASK_ID},
            existing_group_ids={self.GROUP_ID},
            existing_topic_ids={self.TOPIC_ID},
            subtopic_topic_ids={self.SUBTOPIC_ID: self.TOPIC_ID},
            existing_classifications={self.CLASSIFICATION},
        )

        preview = self.service.build(payload, facts)

        self.assertEqual(
            preview['task_uuid_counts'],
            {'existing': 1, 'new': 0, 'invalid': 0},
        )
        self.assertEqual(
            preview['dependency_counts'],
            {
                'missing_topics': 0,
                'missing_subtopics': 0,
                'missing_groups': 0,
                'broken_references': 0,
                'missing_classifications': 0,
            },
        )

    def test_reports_unresolved_external_references(self):
        payload = self._payload()
        payload['topics'] = []
        payload['analog_groups'] = []

        preview = self.service.build(payload, TaskImportPreviewFacts())

        self.assertEqual(
            preview['dependency_counts'],
            {
                'missing_topics': 1,
                'missing_subtopics': 1,
                'missing_groups': 1,
                'broken_references': 1,
                'missing_classifications': 1,
            },
        )

    def _payload(self):
        return {
            'sources': [],
            'topics': [{
                'id': self.TOPIC_ID,
                'name': 'Динамика',
                'subtopics': [{
                    'id': self.SUBTOPIC_ID,
                    'name': 'Силы',
                }],
            }],
            'analog_groups': [{
                'id': self.GROUP_ID,
                'name': 'Силы',
            }],
            'tasks': [{
                'id': self.TASK_ID,
                'text': 'Задача',
                'topic': {'id': self.TOPIC_ID},
                'subtopic': {'id': self.SUBTOPIC_ID},
                'groups': [{
                    'id': self.GROUP_ID,
                    'bank_role': 'control',
                }],
                'codifier_content_entries': [{
                    'subject': 'Физика',
                    'exam_type': 'oge',
                    'year': 2026,
                    'code': '1.1',
                }],
            }],
            'task_images': [],
        }
