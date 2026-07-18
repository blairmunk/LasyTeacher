from unittest import TestCase

from core_logic.entities.curriculum import (
    TopicDetailSubtopic,
    TopicDetailTopic,
)
from core_logic.use_cases.get_topic_detail import GetTopicDetailUseCase


class FakeCurriculumRepository:
    def __init__(self):
        self.topic = TopicDetailTopic(
            pk='topic-1',
            name='Кинематика',
            subject='Физика',
            section='Механика',
            grade_level=9,
            order=1,
            difficulty_level=1,
            difficulty_level_display='Базовый',
        )
        self.subtopics = [
            TopicDetailSubtopic(
                pk='subtopic-1',
                name='Скорость',
                order=1,
            )
        ]

    def get_topic(self, topic_id):
        return self.topic if topic_id == self.topic.pk else None

    def get_topic_detail_subtopics(self, topic_id):
        return self.subtopics


class GetTopicDetailUseCaseTests(TestCase):
    def test_execute_builds_topic_detail_data(self):
        repo = FakeCurriculumRepository()

        data = GetTopicDetailUseCase(curriculum_repo=repo).execute('topic-1')

        self.assertEqual(data.topic, repo.topic)
        self.assertEqual(data.subtopics, repo.subtopics)

    def test_execute_returns_empty_data_for_missing_topic(self):
        repo = FakeCurriculumRepository()

        data = GetTopicDetailUseCase(curriculum_repo=repo).execute('missing-topic')

        self.assertIsNone(data.topic)
        self.assertEqual(data.subtopics, [])
