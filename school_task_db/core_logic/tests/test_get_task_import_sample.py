from unittest import TestCase

from core_logic.use_cases.get_task_import_sample import GetTaskImportSampleUseCase


class GetTaskImportSampleUseCaseTests(TestCase):
    def test_execute_returns_sample_payload_and_filename(self):
        data = GetTaskImportSampleUseCase().execute()

        self.assertEqual(data.filename, 'sample_import.json')
        self.assertEqual(data.payload['version'], '1.1')
        self.assertEqual(len(data.payload['tasks']), 2)
        self.assertEqual(data.payload['task_images'], [])
