import json
from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportFileRequest,
    TaskImportPreviewResult,
)
from core_logic.use_cases.preview_task_import_file import (
    PreviewTaskImportFileUseCase,
)


class FakePreviewTaskImportUseCase:
    def __init__(self, result):
        self.result = result
        self.request = None

    def execute(self, request):
        self.request = request
        return self.result


class PreviewTaskImportFileUseCaseTests(TestCase):
    def test_returns_file_error_without_preview(self):
        preview_use_case = FakePreviewTaskImportUseCase(
            TaskImportPreviewResult(preview={}),
        )
        use_case = PreviewTaskImportFileUseCase(
            preview_task_import_use_case=preview_use_case,
        )

        result = use_case.execute(
            TaskImportFileRequest(
                filename='bad.json',
                file_size=1,
                content=b'{',
            ),
        )

        self.assertFalse(result.success)
        self.assertIn('Невалидный JSON', result.error)
        self.assertIsNone(preview_use_case.request)

    def test_returns_validation_and_preview_for_valid_file(self):
        preview_use_case = FakePreviewTaskImportUseCase(
            TaskImportPreviewResult(preview={'tasks_in_context': 1}),
        )
        use_case = PreviewTaskImportFileUseCase(
            preview_task_import_use_case=preview_use_case,
        )

        result = use_case.execute(
            self._request(
                {
                    'tasks': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440000',
                            'text': 'Задание',
                            'answer': 'Ответ',
                        },
                    ],
                },
            ),
        )

        self.assertTrue(result.success)
        self.assertEqual(result.filename, 'tasks.json')
        self.assertEqual(result.preview, {'tasks_in_context': 1})
        self.assertEqual(preview_use_case.request.data['tasks'][0]['text'], 'Задание')
        self.assertTrue(result.validation['is_valid'])

    def test_adds_preview_warning_to_validation_warnings(self):
        preview_use_case = FakePreviewTaskImportUseCase(
            TaskImportPreviewResult(
                preview=None,
                warning='Preview unavailable',
            ),
        )
        use_case = PreviewTaskImportFileUseCase(
            preview_task_import_use_case=preview_use_case,
        )

        result = use_case.execute(
            self._request(
                {
                    'tasks': [
                        {
                            'id': '550e8400-e29b-41d4-a716-446655440000',
                            'text': 'Задание',
                            'answer': 'Ответ',
                        },
                    ],
                },
            ),
        )

        self.assertTrue(result.success)
        self.assertIn('Preview unavailable', result.validation['warnings'])

    def _request(self, data):
        content = json.dumps(data).encode('utf-8')
        return TaskImportFileRequest(
            filename='tasks.json',
            file_size=len(content),
            content=content,
        )
