from types import SimpleNamespace

from django.test import SimpleTestCase

from infrastructure.services.task_image_presentation import (
    TaskImagePresentationService,
)


class FakeStorage:
    def __init__(self, exists=True):
        self._exists = exists

    def exists(self, name):
        return self._exists


class FakeImageField:
    def __init__(self, *, name='task.png', exists=True, size=1024):
        self.name = name
        self.storage = FakeStorage(exists=exists)
        self.url = f'/media/{name}'
        self.size = size

    def __bool__(self):
        return bool(self.name)


class TaskImagePresentationServiceTests(SimpleTestCase):
    def test_builds_existing_image_display_data(self):
        task_image = SimpleNamespace(
            image=FakeImageField(),
            position='right_40',
            get_position_display=lambda: 'Справа, 40%',
        )

        display = TaskImagePresentationService.build(task_image)

        self.assertTrue(display.has_file)
        self.assertEqual(display.safe_url, '/media/task.png')
        self.assertEqual(display.position_status, '✅ Справа, 40%')

    def test_handles_missing_image_file(self):
        task_image = SimpleNamespace(
            image=FakeImageField(exists=False),
            position='',
            get_position_display=lambda: '',
        )

        display = TaskImagePresentationService.build(task_image)

        self.assertFalse(display.has_file)
        self.assertEqual(display.file_size_human, 'Файл отсутствует')
        self.assertEqual(display.position_status, '⚠️ Позиция не задана')

    def test_resolves_position_css_class(self):
        service = TaskImagePresentationService

        self.assertEqual(service.css_class('right_20'), 'task-image-right-20')
        self.assertEqual(
            service.css_class(''),
            'task-image-bottom-70 task-image-no-position',
        )
        self.assertEqual(service.css_class('unknown'), 'task-image-bottom-70')
