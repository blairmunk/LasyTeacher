from unittest import TestCase

from core_logic.entities.task_import import (
    TaskImportExecutionSubmissionRequest,
    TaskImportFileRequest,
)
from core_logic.use_cases.prepare_task_import_file import (
    MAX_TASK_IMPORT_FILE_SIZE,
    PrepareTaskImportExecutionSubmissionUseCase,
    PrepareTaskImportFileUseCase,
)


class PrepareTaskImportFileUseCaseTests(TestCase):
    def setUp(self):
        self.use_case = PrepareTaskImportFileUseCase()

    def test_execute_parses_valid_json(self):
        result = self.use_case.execute(
            TaskImportFileRequest(
                filename='tasks.json',
                file_size=13,
                content=b'{"tasks": []}',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.filename, 'tasks.json')
        self.assertEqual(result.file_size, 13)
        self.assertEqual(result.data, {'tasks': []})

    def test_execute_rejects_large_file(self):
        result = self.use_case.execute(
            TaskImportFileRequest(
                filename='tasks.json',
                file_size=MAX_TASK_IMPORT_FILE_SIZE + 1,
                content=b'{}',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, 'Файл слишком большой: 50MB (макс: 50MB)')

    def test_execute_rejects_non_utf8_content(self):
        result = self.use_case.execute(
            TaskImportFileRequest(
                filename='tasks.json',
                file_size=1,
                content=b'\xff',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.error, 'Файл не в кодировке UTF-8')

    def test_execute_rejects_invalid_json(self):
        result = self.use_case.execute(
            TaskImportFileRequest(
                filename='tasks.json',
                file_size=1,
                content=b'{',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            'Невалидный JSON: Expecting property name enclosed in double quotes '
            '(строка 1, позиция 2)',
        )


class PrepareTaskImportExecutionSubmissionUseCaseTests(TestCase):
    def test_execute_prepares_import_request(self):
        result = PrepareTaskImportExecutionSubmissionUseCase().execute(
            TaskImportExecutionSubmissionRequest(
                filename='tasks.json',
                file_size=13,
                content=b'{"tasks": []}',
                form_data={
                    'mode': ['replace'],
                    'dry_run': ['true'],
                    'create_missing': ['false'],
                },
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.import_request.data, {'tasks': []})
        self.assertEqual(result.import_request.filename, 'tasks.json')
        self.assertEqual(result.import_request.file_size, 13)
        self.assertEqual(result.import_request.mode, 'replace')
        self.assertTrue(result.import_request.dry_run)
        self.assertFalse(result.import_request.create_missing)

    def test_execute_uses_default_import_options(self):
        result = PrepareTaskImportExecutionSubmissionUseCase().execute(
            TaskImportExecutionSubmissionRequest(
                filename='tasks.json',
                file_size=13,
                content=b'{"tasks": []}',
                form_data={},
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.import_request.mode, 'update')
        self.assertFalse(result.import_request.dry_run)
        self.assertTrue(result.import_request.create_missing)

    def test_execute_returns_file_preparation_error(self):
        result = PrepareTaskImportExecutionSubmissionUseCase().execute(
            TaskImportExecutionSubmissionRequest(
                filename='tasks.json',
                file_size=1,
                content=b'\xff',
                form_data={},
            )
        )

        self.assertFalse(result.success)
        self.assertIsNone(result.import_request)
        self.assertEqual(result.error, 'Файл не в кодировке UTF-8')
