from unittest import TestCase

from core_logic.entities.document import PrintSettingsSpec
from core_logic.use_cases.get_print_settings_editor_data import (
    GetPrintSettingsEditorDataRequest,
    GetPrintSettingsEditorDataUseCase,
)
from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)


class FakePrintSettingsRepository:
    def __init__(self):
        self.document_type = None
        self.print_profiles = [
            PrintSettingsSpec(
                name='Work profile',
                document_type=WORK_DOCUMENT_TYPE,
            )
        ]

    def list_print_settings_specs(self, document_type=''):
        self.document_type = document_type
        return self.print_profiles


class GetPrintSettingsEditorDataUseCaseTests(TestCase):
    def test_returns_document_types_and_profiles(self):
        repo = FakePrintSettingsRepository()

        data = GetPrintSettingsEditorDataUseCase(repo).execute(
            GetPrintSettingsEditorDataRequest(
                document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            )
        )

        self.assertEqual(repo.document_type, REMEDIAL_SHEET_DOCUMENT_TYPE)
        self.assertEqual(data.print_profiles[0].name, 'Work profile')

    def test_can_return_renderable_editor_data_only(self):
        data = GetPrintSettingsEditorDataUseCase().execute(
            GetPrintSettingsEditorDataRequest(
                document_type=WORKSHEET_DOCUMENT_TYPE,
                renderable_only=True,
            )
        )

        document_types = [
            document_type.document_type
            for document_type in data.document_types
        ]
        self.assertEqual(
            document_types,
            [WORK_DOCUMENT_TYPE, REMEDIAL_SHEET_DOCUMENT_TYPE],
        )
        self.assertEqual(data.print_profiles, [])
