from unittest import TestCase

from core_logic.value_objects.task_import import (
    TASK_IMPORT_MODE_SKIP,
    TASK_IMPORT_MODE_STRICT,
    TASK_IMPORT_MODE_UPDATE,
    parse_task_group_import_reference,
    validate_task_import_mode,
)


class TaskImportModeTests(TestCase):
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


class TaskGroupImportReferenceTests(TestCase):
    GROUP_ID = '770e8400-e29b-41d4-a716-446655440001'

    def test_parses_uuid_string_with_default_control_role(self):
        reference = parse_task_group_import_reference(self.GROUP_ID)

        self.assertEqual(reference.group_id, self.GROUP_ID)
        self.assertEqual(reference.bank_role, 'control')

    def test_parses_object_with_explicit_bank_role(self):
        reference = parse_task_group_import_reference({
            'group_id': self.GROUP_ID,
            'bank_role': 'demo',
        })

        self.assertEqual(reference.group_id, self.GROUP_ID)
        self.assertEqual(reference.bank_role, 'demo')

    def test_rejects_invalid_shape_uuid_and_role(self):
        invalid_values = (
            [],
            {},
            'not-a-uuid',
            {'id': self.GROUP_ID, 'bank_role': 'unknown'},
        )

        for value in invalid_values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_task_group_import_reference(value)
