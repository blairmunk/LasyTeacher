from unittest import TestCase

from core_logic.value_objects.task_validation import (
    validate_task_topic_selection,
)


class TaskValidationTests(TestCase):
    def test_accepts_topic_without_subtopic(self):
        self.assertEqual(validate_task_topic_selection('topic-1'), ())

    def test_accepts_subtopic_from_selected_topic(self):
        self.assertEqual(
            validate_task_topic_selection(
                topic_id='topic-1',
                subtopic_id='subtopic-1',
                subtopic_topic_id='topic-1',
            ),
            (),
        )

    def test_rejects_missing_topic(self):
        self.assertEqual(
            validate_task_topic_selection(''),
            ('Тема обязательна для выбора',),
        )

    def test_rejects_subtopic_from_another_topic(self):
        self.assertEqual(
            validate_task_topic_selection(
                topic_id='topic-1',
                subtopic_id='subtopic-1',
                subtopic_topic_id='topic-2',
            ),
            ('Выбранная подтема не принадлежит выбранной теме',),
        )
