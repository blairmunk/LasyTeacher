from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    DocumentTemplateSpec,
)
from core_logic.use_cases.get_document_template_editor_data import (
    GetDocumentTemplateEditorDataRequest,
    GetDocumentTemplateEditorDataUseCase,
)
from core_logic.value_objects.document_recipes import (
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    THEORY_SECTION,
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)


class FakeDocumentTemplateRepository:
    def __init__(self):
        self.template_type = None
        self.templates = [
            DocumentTemplateSpec(
                name='Work template',
                template_type=WORK_DOCUMENT_TYPE,
                sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
            )
        ]

    def list_template_specs(self, template_type=''):
        self.template_type = template_type
        return self.templates

    def get_default_template_spec(self, template_type):
        return None


class GetDocumentTemplateEditorDataUseCaseTests(TestCase):
    def test_returns_catalogs_and_templates_for_document_type(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetDocumentTemplateEditorDataUseCase(
            document_template_repo=repo,
        )

        data = use_case.execute(
            GetDocumentTemplateEditorDataRequest(
                document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            )
        )

        self.assertEqual(repo.template_type, REMEDIAL_SHEET_DOCUMENT_TYPE)
        self.assertEqual(data.templates[0].name, 'Work template')
        section_types = [section.section_type for section in data.sections]
        self.assertIn(ORIGINAL_MISTAKES_SECTION, section_types)
        self.assertNotIn(TASK_LIST_SECTION, section_types)

    def test_can_return_renderable_editor_data_only(self):
        use_case = GetDocumentTemplateEditorDataUseCase()

        data = use_case.execute(
            GetDocumentTemplateEditorDataRequest(
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
        self.assertEqual(data.templates, [])

    def test_can_include_legacy_sections(self):
        use_case = GetDocumentTemplateEditorDataUseCase()

        data = use_case.execute(
            GetDocumentTemplateEditorDataRequest(
                document_type=WORK_DOCUMENT_TYPE,
                include_legacy_sections=True,
            )
        )

        self.assertTrue(any(section.is_legacy for section in data.sections))
