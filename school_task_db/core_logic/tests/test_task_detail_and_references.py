from unittest import TestCase

from core_logic.entities.task import ReferenceElementOption, SelectOption
from core_logic.use_cases.get_task_detail import GetTaskDetailUseCase
from core_logic.use_cases.get_task_reference_options import (
    GetCodifierElementsUseCase,
    GetSubtopicOptionsUseCase,
)


class FakeTaskRepository:
    def __init__(self):
        self.detail_task_id = None
        self.detail_queryset_requested = False
        self.subtopic_topic_id = None
        self.reference_request = None

    def get_detail_tasks(self):
        self.detail_queryset_requested = True
        return ['task-queryset']

    def get_task_detail_groups(self, task_id):
        self.detail_task_id = task_id
        return ['group-1']

    def get_subtopic_options(self, topic_id):
        self.subtopic_topic_id = topic_id
        return [SelectOption(id='subtopic-1', name='Кинематика')]

    def get_reference_element_options(self, subject, category):
        self.reference_request = (subject, category)
        return [ReferenceElementOption(code='1.1', name='Механика')]


class TaskDetailAndReferenceUseCaseTests(TestCase):
    def test_detail_use_case_returns_queryset_and_groups(self):
        repo = FakeTaskRepository()
        use_case = GetTaskDetailUseCase(task_repo=repo)

        queryset = use_case.get_queryset()
        detail = use_case.execute('task-1')

        self.assertEqual(queryset, ['task-queryset'])
        self.assertTrue(repo.detail_queryset_requested)
        self.assertEqual(repo.detail_task_id, 'task-1')
        self.assertEqual(detail.task_groups, ['group-1'])

    def test_subtopic_options_rejects_empty_topic(self):
        repo = FakeTaskRepository()
        use_case = GetSubtopicOptionsUseCase(task_repo=repo)

        result = use_case.execute('')

        self.assertEqual(result.subtopics, [])
        self.assertIsNone(repo.subtopic_topic_id)

    def test_subtopic_options_returns_repository_options(self):
        repo = FakeTaskRepository()
        use_case = GetSubtopicOptionsUseCase(task_repo=repo)

        result = use_case.execute('topic-1')

        self.assertEqual(repo.subtopic_topic_id, 'topic-1')
        self.assertEqual(result.subtopics[0].name, 'Кинематика')

    def test_codifier_options_returns_repository_options(self):
        repo = FakeTaskRepository()
        use_case = GetCodifierElementsUseCase(task_repo=repo)

        result = use_case.execute(subject='physics', category='content')

        self.assertEqual(repo.reference_request, ('physics', 'content'))
        self.assertEqual(result.elements[0].code, '1.1')
