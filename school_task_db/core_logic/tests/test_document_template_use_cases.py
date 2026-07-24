from unittest import TestCase

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    CreatePrintSettingsParams,
    DocumentSectionSpec,
    DocumentTemplateSpec,
    UpdateDocumentTemplateParams,
    UpdatePrintSettingsParams,
)
from core_logic.use_cases.create_document_template import (
    CreateDocumentTemplateUseCase,
    DOCUMENT_TEMPLATE_CREATE_STATUS_INVALID,
)
from core_logic.use_cases.create_print_settings import (
    PRINT_SETTINGS_CREATE_STATUS_CREATED,
    CreatePrintSettingsUseCase,
)
from core_logic.use_cases.get_default_document_template import (
    GetDefaultDocumentTemplateRequest,
    GetDefaultDocumentTemplateUseCase,
)
from core_logic.use_cases.get_document_template import (
    GetDocumentTemplateRequest,
    GetDocumentTemplateUseCase,
)
from core_logic.use_cases.get_document_template_list import (
    GetDocumentTemplateListRequest,
    GetDocumentTemplateListUseCase,
)
from core_logic.use_cases.get_print_settings import (
    GetPrintSettingsRequest,
    GetPrintSettingsUseCase,
)
from core_logic.use_cases.get_print_settings_list import (
    GetPrintSettingsListRequest,
    GetPrintSettingsListUseCase,
)
from core_logic.use_cases.get_default_print_settings import (
    GetDefaultPrintSettingsRequest,
    GetDefaultPrintSettingsUseCase,
)
from core_logic.use_cases.update_document_template import (
    DOCUMENT_TEMPLATE_UPDATE_STATUS_INVALID,
    DOCUMENT_TEMPLATE_UPDATE_STATUS_NOT_FOUND,
    UpdateDocumentTemplateUseCase,
)
from core_logic.use_cases.update_print_settings import (
    PRINT_SETTINGS_UPDATE_STATUS_UPDATED,
    UpdatePrintSettingsUseCase,
)
from core_logic.use_cases.document_template_selection import (
    resolve_document_print_settings_spec as legacy_resolve_print_settings_spec,
    resolve_document_template_spec,
)
from core_logic.use_cases.print_settings_selection import (
    resolve_document_print_settings_spec,
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
        self.updated_params = None
        self.update_exists = True
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

    def list_print_settings_specs(self, document_type=''):
        return self.list_template_specs(template_type=document_type)

    def get_default_template_spec(self, template_type):
        self.default_template_type = template_type
        if template_type == WORKSHEET_DOCUMENT_TYPE:
            return self.templates[0]
        return None

    def get_default_print_settings_spec(self, document_type):
        return self.get_default_template_spec(template_type=document_type)

    def get_template_spec(self, template_id, template_type=''):
        self.requested_template_id = (template_id, template_type)
        if template_id == 'template-1' and template_type == WORKSHEET_DOCUMENT_TYPE:
            return self.templates[0]
        return None

    def get_print_settings_spec(self, print_settings_id, document_type=''):
        return self.get_template_spec(
            template_id=print_settings_id,
            template_type=document_type,
        )

    def create_template(self, params):
        self.created_params = params
        return 'created-template'

    def create_print_settings(self, params):
        return self.create_template(params)

    def update_template(self, params):
        self.updated_params = params
        return self.update_exists

    def update_print_settings(self, params):
        return self.update_template(params)


class GetDocumentTemplateListUseCaseTests(TestCase):
    def test_returns_print_profiles_from_repository(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetDocumentTemplateListUseCase(print_settings_repo=repo)

        data = use_case.execute(
            GetDocumentTemplateListRequest(
                document_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertIs(use_case.print_settings_repo, repo)
        self.assertIs(use_case.document_template_repo, repo)
        self.assertEqual(repo.requested_template_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(data.print_profiles[0].name, 'Рабочий лист')
        self.assertEqual(data.print_profiles[0].section_types, ('header',))
        self.assertEqual(data.templates[0].name, 'Рабочий лист')

    def test_returns_default_template_from_repository(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetDefaultDocumentTemplateUseCase(
            document_template_repo=repo,
        )

        data = use_case.execute(
            GetDefaultDocumentTemplateRequest(
                template_type='legacy-unused',
                document_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertEqual(repo.default_template_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(data.print_profile.name, 'Рабочий лист')
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

        self.assertIsNone(data.print_profile)
        self.assertIsNone(data.template)

    def test_returns_template_by_id(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetDocumentTemplateUseCase(document_template_repo=repo)

        data = use_case.execute(
            GetDocumentTemplateRequest(
                template_id='legacy-unused',
                template_type='legacy-unused',
                print_settings_id='template-1',
                document_type=WORKSHEET_DOCUMENT_TYPE,
            )
        )

        self.assertEqual(data.print_profile.name, 'Рабочий лист')
        self.assertEqual(data.template.name, 'Рабочий лист')
        self.assertEqual(
            repo.requested_template_id,
            ('template-1', WORKSHEET_DOCUMENT_TYPE),
        )

    def test_returns_print_settings_by_clean_identifiers(self):
        repo = FakeDocumentTemplateRepository()
        use_case = GetPrintSettingsUseCase(print_settings_repo=repo)

        data = use_case.execute(
            GetPrintSettingsRequest(
                print_settings_id='template-1',
                document_type=WORKSHEET_DOCUMENT_TYPE,
            )
        )

        self.assertEqual(data.print_profile.name, 'Рабочий лист')
        self.assertEqual(
            repo.requested_template_id,
            ('template-1', WORKSHEET_DOCUMENT_TYPE),
        )

    def test_returns_clean_print_settings_list(self):
        repo = FakeDocumentTemplateRepository()

        data = GetPrintSettingsListUseCase(repo).execute(
            GetPrintSettingsListRequest(
                document_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertEqual(repo.requested_template_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(data.print_profiles[0].name, 'Рабочий лист')
        self.assertFalse(hasattr(data, 'templates'))

    def test_returns_clean_default_print_settings(self):
        repo = FakeDocumentTemplateRepository()

        data = GetDefaultPrintSettingsUseCase(repo).execute(
            GetDefaultPrintSettingsRequest(
                document_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertEqual(repo.default_template_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(data.print_profile.name, 'Рабочий лист')
        self.assertFalse(hasattr(data, 'template'))


class DocumentTemplateSelectionTests(TestCase):
    def test_legacy_module_reexports_print_settings_selection(self):
        self.assertIs(
            legacy_resolve_print_settings_spec,
            resolve_document_print_settings_spec,
        )

    def test_request_print_settings_takes_precedence(self):
        repo = FakeDocumentTemplateRepository()
        request_print_settings = DocumentTemplateSpec(
            name='Из запроса',
            template_type=WORKSHEET_DOCUMENT_TYPE,
            sections=[],
        )

        print_settings = resolve_document_print_settings_spec(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            request_print_settings_spec=request_print_settings,
            print_settings_repo=repo,
        )

        self.assertEqual(print_settings, request_print_settings)
        self.assertIsNone(repo.default_template_type)

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
        self.assertIn('Название профиля печати обязательно.', result.errors)
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

    def test_clean_use_case_creates_print_settings(self):
        repo = FakeDocumentTemplateRepository()
        params = CreatePrintSettingsParams(
            name='Профиль',
            template_type=WORKSHEET_DOCUMENT_TYPE,
            section_types=('header', 'task_list'),
        )

        result = CreatePrintSettingsUseCase(repo).execute(params)

        self.assertEqual(result.status, PRINT_SETTINGS_CREATE_STATUS_CREATED)
        self.assertEqual(result.print_settings_id, 'created-template')
        self.assertIs(repo.created_params, params)


class UpdateDocumentTemplateUseCaseTests(TestCase):
    def test_updates_template_from_valid_params(self):
        repo = FakeDocumentTemplateRepository()
        use_case = UpdateDocumentTemplateUseCase(document_template_repo=repo)
        params = UpdateDocumentTemplateParams(
            template_id='template-1',
            name='  Новый шаблон  ',
            description='  Новое описание  ',
            template_type='work',
            section_types=('header', 'task_list'),
            is_default=True,
        )

        result = use_case.execute(params)

        self.assertTrue(result.success)
        self.assertEqual(result.template_id, 'template-1')
        self.assertEqual(repo.updated_params.name, 'Новый шаблон')
        self.assertEqual(repo.updated_params.description, 'Новое описание')
        self.assertEqual(repo.updated_params.section_types, ('header', 'task_list'))
        self.assertTrue(repo.updated_params.is_default)

    def test_returns_not_found_for_missing_template(self):
        repo = FakeDocumentTemplateRepository()
        repo.update_exists = False
        use_case = UpdateDocumentTemplateUseCase(document_template_repo=repo)

        result = use_case.execute(
            UpdateDocumentTemplateParams(
                template_id='missing',
                name='Шаблон',
                template_type='work',
                section_types=('header',),
            )
        )

        self.assertEqual(result.status, DOCUMENT_TEMPLATE_UPDATE_STATUS_NOT_FOUND)

    def test_rejects_invalid_update(self):
        repo = FakeDocumentTemplateRepository()
        use_case = UpdateDocumentTemplateUseCase(document_template_repo=repo)

        result = use_case.execute(
            UpdateDocumentTemplateParams(
                template_id='template-1',
                name='Шаблон РнО',
                template_type='remedial_sheet',
                section_types=('task_list',),
            )
        )

        self.assertEqual(result.status, DOCUMENT_TEMPLATE_UPDATE_STATUS_INVALID)
        self.assertIsNone(repo.updated_params)

    def test_clean_use_case_updates_print_settings(self):
        repo = FakeDocumentTemplateRepository()
        params = UpdatePrintSettingsParams(
            template_id='template-1',
            name='Профиль',
            template_type=WORKSHEET_DOCUMENT_TYPE,
            section_types=('header', 'task_list'),
        )

        result = UpdatePrintSettingsUseCase(repo).execute(params)

        self.assertEqual(result.status, PRINT_SETTINGS_UPDATE_STATUS_UPDATED)
        self.assertEqual(result.print_settings_id, 'template-1')
        self.assertIs(repo.updated_params, params)
