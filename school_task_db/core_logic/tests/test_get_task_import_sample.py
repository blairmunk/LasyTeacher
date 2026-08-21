from unittest import TestCase

from core_logic.use_cases.get_task_import_sample import GetTaskImportSampleUseCase


class GetTaskImportSampleUseCaseTests(TestCase):
    def test_execute_returns_sample_payload_and_filename(self):
        data = GetTaskImportSampleUseCase().execute()

        self.assertEqual(data.filename, 'sample_import.json')
        self.assertEqual(data.payload['version'], '1.5')
        self.assertIn('id', data.payload['topics'][0])
        self.assertEqual(
            data.payload['tasks'][0]['topic'],
            {'id': '660e8400-e29b-41d4-a716-446655440001'},
        )
        self.assertEqual(
            data.payload['tasks'][0]['groups'][0]['bank_role'],
            'demo',
        )
        self.assertEqual(len(data.payload['tasks']), 2)
        self.assertEqual(data.payload['task_images'], [])
