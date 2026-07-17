from unittest import TestCase

from core_logic.use_cases.get_topic_subtopics import (
    GetTopicSubtopicsUseCase,
    TopicSubtopicsRequest,
)


class FakeCurriculumRepository:
    def __init__(self):
        self.topic_id = None

    def get_topic_subtopics(self, topic_id):
        self.topic_id = topic_id
        return [{
            'id': 'subtopic-1',
            'name': 'Скорость',
            'description': '',
        }]


class GetTopicSubtopicsUseCaseTests(TestCase):
    def test_execute_returns_serialized_subtopics(self):
        repo = FakeCurriculumRepository()
        use_case = GetTopicSubtopicsUseCase(curriculum_repo=repo)

        data = use_case.execute(TopicSubtopicsRequest(topic_id='topic-1'))

        self.assertEqual(repo.topic_id, 'topic-1')
        self.assertEqual(data.subtopics, [{
            'id': 'subtopic-1',
            'name': 'Скорость',
            'description': '',
        }])
