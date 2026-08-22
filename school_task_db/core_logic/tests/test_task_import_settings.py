from unittest import TestCase

from core_logic.value_objects.task_import import (
    TASK_IMPORT_ACTION_CREATE,
    TASK_IMPORT_ACTION_SKIP,
    TASK_IMPORT_ACTION_UPDATE,
    TASK_IMPORT_MODE_SKIP,
    TASK_IMPORT_MODE_STRICT,
    TASK_IMPORT_MODE_UPDATE,
    TaskImportConflictError,
    normalize_task_import_uuid,
    parse_task_group_import_reference,
    task_import_action,
    validate_task_import_mode,
)


class TaskImportUuidTests(TestCase):
    UUID = '550e8400-e29b-41d4-a716-446655440001'

    def test_normalizes_uuid_to_canonical_lowercase(self):
        self.assertEqual(
            normalize_task_import_uuid(self.UUID.upper()),
            self.UUID,
        )

    def test_rejects_missing_and_invalid_uuid_values(self):
        for value in (None, '', 'not-a-uuid', object()):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_task_import_uuid(value)


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

    def test_new_object_is_created_in_every_mode(self):
        for mode in (
            TASK_IMPORT_MODE_STRICT,
            TASK_IMPORT_MODE_UPDATE,
            TASK_IMPORT_MODE_SKIP,
        ):
            with self.subTest(mode=mode):
                self.assertEqual(
                    task_import_action(mode, exists=False),
                    TASK_IMPORT_ACTION_CREATE,
                )

    def test_existing_object_is_updated_or_skipped_by_mode(self):
        self.assertEqual(
            task_import_action(TASK_IMPORT_MODE_UPDATE, exists=True),
            TASK_IMPORT_ACTION_UPDATE,
        )
        self.assertEqual(
            task_import_action(TASK_IMPORT_MODE_SKIP, exists=True),
            TASK_IMPORT_ACTION_SKIP,
        )

    def test_strict_mode_rejects_existing_object(self):
        with self.assertRaisesRegex(
            TaskImportConflictError,
            '55667788',
        ):
            task_import_action(
                TASK_IMPORT_MODE_STRICT,
                exists=True,
                object_id='11223344-55667788',
            )


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
