from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    DocumentTemplateSpec,
)
from core_logic.use_cases.get_document_template_list import (
    GetDocumentTemplateListRequest,
    GetDocumentTemplateListUseCase,
)


class FakeDocumentTemplateRepository:
    def __init__(self):
        self.requested_template_type = None
        self.templates = [
            DocumentTemplateSpec(
                name='Рабочий лист',
                template_type='worksheet',
                sections=[DocumentSectionSpec(section_type='header')],
            )
        ]

    def list_template_specs(self, template_type=''):
        self.requested_template_type = template_type
        return self.templates

    def get_default_template_spec(self, template_type):
        return None


class GetDocumentTemplateListUseCaseTests(TestCase):
    def test_returns_templates_from_repository(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetDocumentTemplateListUseCase(document_template_repo=repo)

        data = use_case.execute(
            GetDocumentTemplateListRequest(template_type='worksheet'),
        )

        self.assertEqual(repo.requested_template_type, 'worksheet')
        self.assertEqual(data.templates[0].name, 'Рабочий лист')
        self.assertEqual(data.templates[0].section_types, ('header',))
