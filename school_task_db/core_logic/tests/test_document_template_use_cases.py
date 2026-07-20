from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    DocumentTemplateSpec,
)
from core_logic.use_cases.get_default_document_template import (
    GetDefaultDocumentTemplateRequest,
    GetDefaultDocumentTemplateUseCase,
)
from core_logic.use_cases.get_document_template_list import (
    GetDocumentTemplateListRequest,
    GetDocumentTemplateListUseCase,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)


class FakeDocumentTemplateRepository:
    def __init__(self):
        self.requested_template_type = None
        self.default_template_type = None
        self.templates = [
            DocumentTemplateSpec(
                name='Рабочий лист',
                template_type=WORKSHEET_DOCUMENT_TYPE,
                sections=[DocumentSectionSpec(section_type='header')],
            )
        ]

    def list_template_specs(self, template_type=''):
        self.requested_template_type = template_type
        return self.templates

    def get_default_template_spec(self, template_type):
        self.default_template_type = template_type
        if template_type == WORKSHEET_DOCUMENT_TYPE:
            return self.templates[0]
        return None


class GetDocumentTemplateListUseCaseTests(TestCase):
    def test_returns_templates_from_repository(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetDocumentTemplateListUseCase(document_template_repo=repo)

        data = use_case.execute(
            GetDocumentTemplateListRequest(
                template_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertEqual(repo.requested_template_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(data.templates[0].name, 'Рабочий лист')
        self.assertEqual(data.templates[0].section_types, ('header',))

    def test_returns_default_template_from_repository(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetDefaultDocumentTemplateUseCase(
            document_template_repo=repo,
        )

        data = use_case.execute(
            GetDefaultDocumentTemplateRequest(
                template_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertEqual(repo.default_template_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(data.template.name, 'Рабочий лист')

    def test_returns_none_for_missing_default_template(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetDefaultDocumentTemplateUseCase(
            document_template_repo=repo,
        )

        data = use_case.execute(
            GetDefaultDocumentTemplateRequest(
                template_type=ANSWER_KEY_DOCUMENT_TYPE,
            ),
        )

        self.assertIsNone(data.template)
