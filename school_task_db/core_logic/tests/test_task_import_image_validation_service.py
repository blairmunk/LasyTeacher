from unittest import TestCase

from core_logic.services.task_import_image_validation_service import (
    TaskImportImageValidationService,
)


class TaskImportImageValidationServiceTests(TestCase):
    TASK_ID = '550e8400-e29b-41d4-a716-446655440001'
    IMAGE_ID = '990e8400-e29b-41d4-a716-446655440001'

    def setUp(self):
        self.service = TaskImportImageValidationService()

    def test_accepts_exported_image_record_and_data_uri(self):
        result = self.service.validate([{
            'id': self.IMAGE_ID.upper(),
            'task_id': self.TASK_ID.upper(),
            'filename': 'diagram.png',
            'position': 'bottom_70',
            'caption': 'Схема',
            'order': 1,
            'base64_data': 'data:image/png;base64,aW1hZ2U=',
        }], declared_task_ids={self.TASK_ID})

        self.assertEqual(result.total, 1)
        self.assertEqual(result.errors, ())
        self.assertEqual(result.warnings, ())

    def test_rejects_non_list_image_catalog(self):
        result = self.service.validate(
            {'id': self.IMAGE_ID},
            declared_task_ids={self.TASK_ID},
        )

        self.assertEqual(result.total, 0)
        self.assertEqual(
            result.errors,
            ('"task_images" должен быть массивом',),
        )

    def test_rejects_invalid_identity_metadata_and_content(self):
        result = self.service.validate([
            'not-an-object',
            {
                'id': 'not-a-uuid',
                'task_id': 'also-not-a-uuid',
                'position': 'somewhere',
                'order': -1,
                'base64_data': 'not-base64!',
            },
        ], declared_task_ids={self.TASK_ID})

        self.assertEqual(result.total, 2)
        self.assertTrue(any('должно быть объектом' in error for error in result.errors))
        self.assertTrue(any('некорректный id UUID' in error for error in result.errors))
        self.assertTrue(any('некорректный task_id UUID' in error for error in result.errors))
        self.assertTrue(any('position' in error for error in result.errors))
        self.assertTrue(any('order' in error for error in result.errors))
        self.assertTrue(any('base64_data' in error for error in result.errors))

    def test_rejects_duplicate_image_ids_independent_of_case(self):
        records = [
            self._record(id=self.IMAGE_ID),
            self._record(id=self.IMAGE_ID.upper()),
        ]

        result = self.service.validate(
            records,
            declared_task_ids={self.TASK_ID},
        )

        self.assertTrue(any(
            'дублирующийся id' in error
            for error in result.errors
        ))

    def test_allows_metadata_only_update_with_warning(self):
        record = self._record()
        record.pop('base64_data')

        result = self.service.validate(
            [record],
            declared_task_ids={self.TASK_ID},
        )

        self.assertEqual(result.errors, ())
        self.assertEqual(len(result.warnings), 1)
        self.assertIn('нет base64_data', result.warnings[0])

    def _record(self, **overrides):
        return {
            'id': self.IMAGE_ID,
            'task_id': self.TASK_ID,
            'base64_data': 'aW1hZ2U=',
            **overrides,
        }
