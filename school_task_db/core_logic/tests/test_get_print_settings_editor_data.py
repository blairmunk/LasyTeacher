from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    PrintSettingsSpec,
)
from core_logic.use_cases.get_print_settings_editor_data import (
    GetPrintSettingsEditorDataRequest,
    GetPrintSettingsEditorDataUseCase,
)
from core_logic.value_objects.document_recipes import (
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    THEORY_SECTION,
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
                sections=[DocumentSectionSpec(section_type='header')],
            )
        ]

    def list_print_settings_specs(self, document_type=''):
        self.document_type = document_type
        return self.print_profiles


class GetPrintSettingsEditorDataUseCaseTests(TestCase):
    def test_returns_catalogs_and_profiles_for_document_type(self):
        repo = FakePrintSettingsRepository()

        data = GetPrintSettingsEditorDataUseCase(repo).execute(
            GetPrintSettingsEditorDataRequest(
                document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            )
        )

        self.assertEqual(repo.document_type, REMEDIAL_SHEET_DOCUMENT_TYPE)
        self.assertEqual(data.print_profiles[0].name, 'Work profile')
        section_types = [section.section_type for section in data.sections]
        self.assertIn(ORIGINAL_MISTAKES_SECTION, section_types)
        self.assertNotIn(TASK_LIST_SECTION, section_types)

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
        section_types = [section.section_type for section in data.sections]
        self.assertEqual(
            document_types,
            [WORK_DOCUMENT_TYPE, REMEDIAL_SHEET_DOCUMENT_TYPE],
        )
        self.assertNotIn(THEORY_SECTION, section_types)
        self.assertEqual(data.print_profiles, [])

    def test_can_include_legacy_sections(self):
        data = GetPrintSettingsEditorDataUseCase().execute(
            GetPrintSettingsEditorDataRequest(
                document_type=WORK_DOCUMENT_TYPE,
                include_legacy_sections=True,
            )
        )

        self.assertTrue(any(section.is_legacy for section in data.sections))
