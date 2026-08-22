from unittest import TestCase

from core_logic.value_objects.task_content_snapshot import (
    TaskCodifierSnapshot,
    TaskContentSnapshot,
    TaskImageSnapshot,
    task_content_snapshot_payload,
)


class TaskContentSnapshotTests(TestCase):
    def test_round_trips_through_json_compatible_mapping(self):
        snapshot = TaskContentSnapshot(
            task_id='task-1',
            text='Условие',
            answer='Ответ',
            topic_name='Динамика',
            codifier_content_entries=(
                TaskCodifierSnapshot(
                    codifier_id='codifier-1',
                    codifier_name='ОГЭ по физике',
                    codifier_short_name='ОГЭ',
                    code='1.2',
                    name='Динамика',
                ),
            ),
            codifier_requirements=(
                TaskCodifierSnapshot(
                    codifier_id='codifier-1',
                    codifier_name='ОГЭ по физике',
                    codifier_short_name='ОГЭ',
                    code='2.3',
                    name='Применять законы',
                ),
            ),
            content_element_descriptions=('ОГЭ: Динамика',),
        )

        restored = TaskContentSnapshot.from_mapping(snapshot.to_mapping())

        self.assertEqual(restored, snapshot)

    def test_rejects_missing_snapshot(self):
        with self.assertRaisesRegex(ValueError, 'no task content snapshot'):
            TaskContentSnapshot.from_mapping({})

    def test_projects_snapshot_to_document_payload(self):
        snapshot = TaskContentSnapshot(
            task_id='task-1',
            text='Условие',
            answer='Ответ',
            topic_name='Динамика',
            source_name='Сборник',
            codifier_content_entries=(
                TaskCodifierSnapshot(
                    codifier_id='codifier-1',
                    codifier_name='ОГЭ по физике',
                    codifier_short_name='ОГЭ',
                    code='1.2',
                    name='Динамика',
                ),
            ),
            codifier_requirements=(
                TaskCodifierSnapshot(
                    codifier_id='codifier-1',
                    codifier_name='ОГЭ по физике',
                    codifier_short_name='ОГЭ',
                    code='2.3',
                    name='Применять законы',
                ),
            ),
            images=(
                TaskImageSnapshot(
                    image_id='image-1',
                    asset_id='asset-1',
                    file_name='tasks/image.png',
                    position='bottom',
                    caption='Рисунок',
                ),
            ),
        )

        payload = task_content_snapshot_payload(snapshot.to_mapping())

        self.assertEqual(payload['id'], 'task-1')
        self.assertEqual(payload['text'], 'Условие')
        self.assertEqual(payload['topic'], 'Динамика')
        self.assertEqual(payload['source'], 'Сборник')
        self.assertEqual(
            payload['codifier_content_entries'][0]['code'],
            '1.2',
        )
        self.assertEqual(
            payload['codifier_requirements'][0]['code'],
            '2.3',
        )
        self.assertEqual(payload['images'][0]['image_id'], 'image-1')
        self.assertEqual(payload['images'][0]['asset_id'], 'asset-1')
