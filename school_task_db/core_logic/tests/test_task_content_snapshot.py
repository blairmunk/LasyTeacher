from unittest import TestCase

from core_logic.value_objects.task_content_snapshot import (
    TaskCodifierSnapshot,
    TaskContentSnapshot,
)


class TaskContentSnapshotTests(TestCase):
    def test_round_trips_through_json_compatible_mapping(self):
        snapshot = TaskContentSnapshot(
            task_id='task-1',
            text='Условие',
            answer='Ответ',
            topic_name='Динамика',
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
