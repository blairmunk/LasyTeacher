from django.test import SimpleTestCase

from core_logic.value_objects.task_import import (
    TASK_IMPORT_MODE_SKIP,
    TASK_IMPORT_MODE_STRICT,
    TASK_IMPORT_MODE_UPDATE,
    validate_task_import_mode,
)


class TaskImportModeTests(SimpleTestCase):
    def test_supported_modes_are_returned_unchanged(self):
        for mode in (
            TASK_IMPORT_MODE_STRICT,
            TASK_IMPORT_MODE_UPDATE,
            TASK_IMPORT_MODE_SKIP,
        ):
            with self.subTest(mode=mode):
                self.assertEqual(validate_task_import_mode(mode), mode)

    def test_unsupported_mode_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Неверный режим импорта'):
            validate_task_import_mode('replace')
