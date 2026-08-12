from unittest import TestCase

from core_logic.entities.task import (
    SelectOption,
    TaskClassificationOptions,
    TaskDetailGroup,
    TaskDetailTask,
)
from core_logic.use_cases.get_task_detail import GetTaskDetailUseCase
from core_logic.use_cases.get_task_reference_options import (
    GetSubtopicOptionsUseCase,
)
from core_logic.use_cases.get_task_classification_options import (
    GetTaskClassificationOptionsUseCase,
)


class FakeTaskRepository:
    def __init__(self):
        self.task = TaskDetailTask(
            pk='task-1',
            topic='Кинематика',
            section='Механика',
            text='Задача',
            answer='Ответ',
            task_type_display='Расчётная задача',
            difficulty_display='Базовый',
            short_uuid='abcd1234',
            images=[],
        )
        self.groups = [TaskDetailGroup(pk='group-1', name='Скорость')]
        self.detail_task_id = None
        self.subtopic_topic_id = None

    def get_task(self, task_id):
        return self.task if task_id == self.task.pk else None

    def get_task_detail_groups(self, task_id):
        self.detail_task_id = task_id
        return self.groups

    def get_subtopic_options(self, topic_id):
        self.subtopic_topic_id = topic_id
        return [SelectOption(id='subtopic-1', name='Кинематика')]


class FakeTaskClassificationRepository:
    def __init__(self):
        self.topic_id = None

    def get_classification_options(self, topic_id):
        self.topic_id = topic_id
        return TaskClassificationOptions(
            content_entries=[SelectOption(id='content-1', name='1.1 · Сила')],
            requirements=[SelectOption(id='requirement-1', name='2.1 · Решать')],
        )



class TaskDetailAndReferenceUseCaseTests(TestCase):
    def test_detail_use_case_returns_task_and_groups(self):
        repo = FakeTaskRepository()
        use_case = GetTaskDetailUseCase(task_repo=repo)

        detail = use_case.execute('task-1')

        self.assertEqual(detail.task, repo.task)
        self.assertEqual(repo.detail_task_id, 'task-1')
        self.assertEqual(detail.task_groups, repo.groups)

    def test_detail_use_case_returns_empty_data_for_missing_task(self):
        repo = FakeTaskRepository()
        use_case = GetTaskDetailUseCase(task_repo=repo)

        detail = use_case.execute('missing-task')

        self.assertIsNone(detail.task)
        self.assertIsNone(detail.task_groups)
        self.assertIsNone(repo.detail_task_id)

    def test_subtopic_options_rejects_empty_topic(self):
        repo = FakeTaskRepository()
        use_case = GetSubtopicOptionsUseCase(task_catalog_repo=repo)

        result = use_case.execute('')

        self.assertEqual(result.subtopics, [])
        self.assertIsNone(repo.subtopic_topic_id)

    def test_subtopic_options_returns_repository_options(self):
        repo = FakeTaskRepository()
        use_case = GetSubtopicOptionsUseCase(task_catalog_repo=repo)

        result = use_case.execute('topic-1')

        self.assertEqual(repo.subtopic_topic_id, 'topic-1')
        self.assertEqual(result.subtopics[0].name, 'Кинематика')

    def test_classification_options_reject_empty_topic(self):
        repo = FakeTaskClassificationRepository()
        use_case = GetTaskClassificationOptionsUseCase(repo)

        result = use_case.execute('')

        self.assertEqual(result.content_entries, [])
        self.assertEqual(result.requirements, [])
        self.assertIsNone(repo.topic_id)

    def test_classification_options_return_repository_values(self):
        repo = FakeTaskClassificationRepository()
        use_case = GetTaskClassificationOptionsUseCase(repo)

        result = use_case.execute('topic-1')

        self.assertEqual(repo.topic_id, 'topic-1')
        self.assertEqual(result.content_entries[0].id, 'content-1')
        self.assertEqual(result.requirements[0].id, 'requirement-1')
