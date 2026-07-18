from django.test import SimpleTestCase

from core_logic.entities.curriculum import TopicListItem
from core_logic.use_cases.get_topic_list import GetTopicListUseCase


class FakeCurriculumRepository:
    def __init__(self):
        self.topics = [
            TopicListItem(
                pk='topic-1',
                name='Кинематика',
                subject='Физика',
                section='Механика',
                grade_level=9,
                order=1,
                difficulty_level=1,
                difficulty_level_display='Базовый',
                subtopics_count=2,
            )
        ]

    def get_topics(self):
        return self.topics


class GetTopicListUseCaseTests(SimpleTestCase):
    def test_execute_returns_topic_list_data(self):
        repo = FakeCurriculumRepository()

        data = GetTopicListUseCase(curriculum_repo=repo).execute()

        self.assertEqual(data.topics, repo.topics)
        self.assertEqual(data.topics[0].subtopics_count, 2)
