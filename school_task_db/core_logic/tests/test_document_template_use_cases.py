from unittest import TestCase

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    DocumentSectionSpec,
    DocumentTemplateSpec,
)
from core_logic.use_cases.create_document_template import (
    CreateDocumentTemplateUseCase,
    DOCUMENT_TEMPLATE_CREATE_STATUS_INVALID,
)
from core_logic.use_cases.get_default_document_template import (
    GetDefaultDocumentTemplateRequest,
    GetDefaultDocumentTemplateUseCase,
)
from core_logic.use_cases.get_document_template_list import (
    GetDocumentTemplateListRequest,
    GetDocumentTemplateListUseCase,
)
from core_logic.use_cases.document_template_selection import (
    resolve_document_template_spec,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)


class FakeDocumentTemplateRepository:
    def __init__(self):
        self.requested_template_type = None
        self.default_template_type = None
        self.requested_template_id = None
        self.created_params = None
        self.templates = [
            DocumentTemplateSpec(
                name='Рабочий лист',
                template_type=WORKSHEET_DOCUMENT_TYPE,
                template_id='template-1',
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

    def get_template_spec(self, template_id, template_type=''):
        self.requested_template_id = (template_id, template_type)
        if template_id == 'template-1' and template_type == WORKSHEET_DOCUMENT_TYPE:
            return self.templates[0]
        return None

    def create_template(self, params):
        self.created_params = params
        return 'created-template'


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


class DocumentTemplateSelectionTests(TestCase):
    def test_request_template_takes_precedence(self):
        repo = FakeDocumentTemplateRepository()
        request_template = DocumentTemplateSpec(
            name='Из запроса',
            template_type=WORKSHEET_DOCUMENT_TYPE,
            sections=[],
        )

        template = resolve_document_template_spec(
            template_type=WORKSHEET_DOCUMENT_TYPE,
            request_template_spec=request_template,
            document_template_repo=repo,
        )

        self.assertEqual(template, request_template)
        self.assertIsNone(repo.default_template_type)

    def test_returns_default_template_from_repository(self):
        repo = FakeDocumentTemplateRepository()

        template = resolve_document_template_spec(
            template_type=WORKSHEET_DOCUMENT_TYPE,
            document_template_repo=repo,
        )

        self.assertEqual(repo.default_template_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(template.name, 'Рабочий лист')

    def test_returns_template_by_id_from_repository(self):
        repo = FakeDocumentTemplateRepository()

        template = resolve_document_template_spec(
            template_type=WORKSHEET_DOCUMENT_TYPE,
            request_template_id='template-1',
            document_template_repo=repo,
        )

        self.assertEqual(
            repo.requested_template_id,
            ('template-1', WORKSHEET_DOCUMENT_TYPE),
        )
        self.assertEqual(template.name, 'Рабочий лист')
        self.assertIsNone(repo.default_template_type)

    def test_returns_none_without_repository(self):
        template = resolve_document_template_spec(
            template_type=WORKSHEET_DOCUMENT_TYPE,
        )

        self.assertIsNone(template)


class CreateDocumentTemplateUseCaseTests(TestCase):
    def test_creates_template_from_valid_params(self):
        repo = FakeDocumentTemplateRepository()
        use_case = CreateDocumentTemplateUseCase(document_template_repo=repo)
        params = CreateDocumentTemplateParams(
            name='  Шаблон работы  ',
            description='  Для печати  ',
            template_type='work',
            section_types=('header', 'task_list'),
            is_default=True,
        )

        result = use_case.execute(params)

        self.assertTrue(result.success)
        self.assertEqual(result.template_id, 'created-template')
        self.assertEqual(repo.created_params.name, 'Шаблон работы')
        self.assertEqual(repo.created_params.description, 'Для печати')
        self.assertEqual(repo.created_params.section_types, ('header', 'task_list'))
        self.assertTrue(repo.created_params.is_default)

    def test_rejects_missing_required_fields(self):
        repo = FakeDocumentTemplateRepository()
        use_case = CreateDocumentTemplateUseCase(document_template_repo=repo)

        result = use_case.execute(
            CreateDocumentTemplateParams(
                name='',
                template_type='',
                section_types=(),
            )
        )

        self.assertEqual(result.status, DOCUMENT_TEMPLATE_CREATE_STATUS_INVALID)
        self.assertIn('Название шаблона обязательно.', result.errors)
        self.assertIn('Тип документа обязателен.', result.errors)
        self.assertIn('Выберите хотя бы одну секцию.', result.errors)
        self.assertIsNone(repo.created_params)

    def test_rejects_section_for_wrong_document_type(self):
        repo = FakeDocumentTemplateRepository()
        use_case = CreateDocumentTemplateUseCase(document_template_repo=repo)

        result = use_case.execute(
            CreateDocumentTemplateParams(
                name='Шаблон РнО',
                template_type='remedial_sheet',
                section_types=('task_list',),
            )
        )

        self.assertEqual(result.status, DOCUMENT_TEMPLATE_CREATE_STATUS_INVALID)
        self.assertIn(
            'Section task_list is not supported for document type remedial_sheet',
            result.errors,
        )
        self.assertIsNone(repo.created_params)
