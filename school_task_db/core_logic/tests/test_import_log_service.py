from unittest import TestCase

from core_logic.services.import_log_service import ImportLogService


class ImportLogServiceTests(TestCase):
    def test_calculates_processed_total_and_status_icon(self):
        self.assertEqual(ImportLogService.total_processed(2, 3, 4), 9)
        self.assertEqual(ImportLogService.status_icon('success'), '✅')
        self.assertEqual(ImportLogService.status_icon('unknown'), '❓')

    def test_formats_duration(self):
        self.assertEqual(ImportLogService.duration_human(999), '999 мс')
        self.assertEqual(ImportLogService.duration_human(1500), '1.5 с')

    def test_formats_file_size(self):
        self.assertEqual(ImportLogService.file_size_human(1000), '1000 Б')
        self.assertEqual(ImportLogService.file_size_human(1536), '1.5 КБ')
        self.assertEqual(
            ImportLogService.file_size_human(2 * 1024 * 1024),
            '2.0 МБ',
        )
