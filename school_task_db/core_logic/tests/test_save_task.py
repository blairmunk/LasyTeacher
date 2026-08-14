from unittest import TestCase

from core_logic.entities.task import (
    TaskImageSaveParams,
    TaskImagesSaveResult,
    TaskSaveParams,
    TaskSaveResult,
)
from core_logic.use_cases.save_task import (
    CreateTaskUseCase,
    SaveTaskImagesUseCase,
    UpdateTaskUseCase,
)


class FakeUploadedFile:
    name = 'task.png'

    def read(self, size=-1):
        return b'image' if size != 0 else b''

    def chunks(self, chunk_size=None):
        yield b'image'


class FakeTaskRepository:
    def __init__(self):
        self.created_params = None
        self.updated_params = None
        self.saved_images = None
        self.subtopic_topics = {}
        self.classification_errors = ()

    def get_subtopic_topic_id(self, subtopic_id):
        return self.subtopic_topics.get(subtopic_id)

    def get_classification_errors(
        self,
        topic_id,
        content_entry_ids,
        requirement_ids,
    ):
        return self.classification_errors

    def create_task(self, params):
        self.created_params = params
        return TaskSaveResult(status='created', task_id='task-1')

    def update_task(self, params):
        self.updated_params = params
        return TaskSaveResult(status='updated', task_id=params.task_id)

    def save_task_images(self, task_id, images):
        self.saved_images = (task_id, images)
        return TaskImagesSaveResult(status='saved', created_images=1)


class SaveTaskUseCaseTests(TestCase):
    def test_create_task_delegates_to_repository(self):
        repo = FakeTaskRepository()
        params = TaskSaveParams(
            text='Задача',
            answer='Ответ',
            topic_id='topic-1',
            task_type='computational',
            difficulty=2,
        )

        result = CreateTaskUseCase(repo, repo, repo).execute(params)

        self.assertEqual(result.task_id, 'task-1')
        self.assertEqual(repo.created_params, params)

    def test_update_task_delegates_to_repository(self):
        repo = FakeTaskRepository()
        params = TaskSaveParams(
            task_id='task-1',
            text='Задача',
            answer='Ответ',
            topic_id='topic-1',
            task_type='computational',
            difficulty=2,
        )

        result = UpdateTaskUseCase(repo, repo, repo).execute(params)

        self.assertEqual(result.status, 'updated')
        self.assertEqual(repo.updated_params, params)

    def test_create_task_rejects_subtopic_from_another_topic(self):
        repo = FakeTaskRepository()
        repo.subtopic_topics['subtopic-1'] = 'topic-2'
        params = TaskSaveParams(
            text='Задача',
            answer='Ответ',
            topic_id='topic-1',
            subtopic_id='subtopic-1',
            task_type='computational',
            difficulty=2,
        )

        result = CreateTaskUseCase(repo, repo, repo).execute(params)

        self.assertEqual(result.status, 'invalid')
        self.assertEqual(
            result.errors,
            ('Выбранная подтема не принадлежит выбранной теме',),
        )
        self.assertIsNone(repo.created_params)

    def test_create_task_rejects_invalid_explicit_classification(self):
        repo = FakeTaskRepository()
        repo.classification_errors = ('Элемент другого предмета',)
        params = TaskSaveParams(
            text='Задача',
            answer='Ответ',
            topic_id='topic-1',
            task_type='computational',
            difficulty=2,
            content_entry_ids=('entry-1',),
        )

        result = CreateTaskUseCase(repo, repo, repo).execute(params)

        self.assertEqual(result.status, 'invalid')
        self.assertEqual(result.errors, ('Элемент другого предмета',))
        self.assertIsNone(repo.created_params)

    def test_save_task_images_delegates_to_repository(self):
        repo = FakeTaskRepository()
        images = [TaskImageSaveParams(image=FakeUploadedFile())]

        result = SaveTaskImagesUseCase(repo).execute(
            task_id='task-1',
            images=images,
        )

        self.assertEqual(result.status, 'saved')
        self.assertEqual(result.created_images, 1)
        self.assertEqual(repo.saved_images, ('task-1', tuple(images)))
