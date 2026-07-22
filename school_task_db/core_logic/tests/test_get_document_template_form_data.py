from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    DocumentTemplateSpec,
)
from core_logic.use_cases.get_document_template_form_data import (
    GetDocumentTemplateFormDataRequest,
    GetDocumentTemplateFormDataUseCase,
)
from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)


class FakeDocumentTemplateRepository:
    def __init__(self, template=None):
        self.template = template
        self.template_id = None

    def get_template_spec(self, template_id, template_type=''):
        self.template_id = template_id
        return self.template


class GetDocumentTemplateFormDataUseCaseTests(TestCase):
    def test_returns_renderable_types_and_sections_for_create_form(self):
        data = GetDocumentTemplateFormDataUseCase().execute()

        self.assertEqual(
            [item.document_type for item in data.document_types],
            [WORK_DOCUMENT_TYPE, REMEDIAL_SHEET_DOCUMENT_TYPE],
        )
        self.assertTrue(data.sections)
        self.assertTrue(
            all(section.renderable_document_types for section in data.sections),
        )
        self.assertIsNone(data.template)

    def test_loads_template_for_update_form(self):
        template = DocumentTemplateSpec(
            template_id='template-1',
            name='Шаблон',
            template_type=WORK_DOCUMENT_TYPE,
            sections=(DocumentSectionSpec(section_type='header'),),
        )
        repo = FakeDocumentTemplateRepository(template=template)

        data = GetDocumentTemplateFormDataUseCase(
            document_template_repo=repo,
        ).execute(
            GetDocumentTemplateFormDataRequest(template_id='template-1'),
        )

        self.assertEqual(repo.template_id, 'template-1')
        self.assertEqual(data.template, template)
