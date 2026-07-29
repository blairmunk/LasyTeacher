from unittest import TestCase

from core_logic.entities.document import (
    CreatePrintSettingsParams,
    PrintSettingsSpec,
    UpdatePrintSettingsParams,
)
from core_logic.use_cases.create_print_settings import (
    PRINT_SETTINGS_CREATE_STATUS_CREATED,
    PRINT_SETTINGS_CREATE_STATUS_INVALID,
    CreatePrintSettingsUseCase,
)
from core_logic.use_cases.get_default_print_settings import (
    GetDefaultPrintSettingsRequest,
    GetDefaultPrintSettingsUseCase,
)
from core_logic.use_cases.get_print_settings import (
    GetPrintSettingsRequest,
    GetPrintSettingsUseCase,
)
from core_logic.use_cases.get_print_settings_list import (
    GetPrintSettingsListRequest,
    GetPrintSettingsListUseCase,
)
from core_logic.use_cases.print_settings_selection import (
    resolve_document_print_settings_spec,
)
from core_logic.use_cases.update_print_settings import (
    PRINT_SETTINGS_UPDATE_STATUS_INVALID,
    PRINT_SETTINGS_UPDATE_STATUS_NOT_FOUND,
    PRINT_SETTINGS_UPDATE_STATUS_UPDATED,
    UpdatePrintSettingsUseCase,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)


class FakePrintSettingsRepository:
    def __init__(self):
        self.requested_document_type = None
        self.default_document_type = None
        self.requested_print_settings_id = None
        self.created_params = None
        self.updated_params = None
        self.update_exists = True
        self.print_profiles = [
            PrintSettingsSpec(
                name='Рабочий лист',
                document_type=WORKSHEET_DOCUMENT_TYPE,
                print_settings_id='profile-1',
            )
        ]

    def list_print_settings_specs(self, document_type=''):
        self.requested_document_type = document_type
        return self.print_profiles

    def get_default_print_settings_spec(self, document_type):
        self.default_document_type = document_type
        if document_type == WORKSHEET_DOCUMENT_TYPE:
            return self.print_profiles[0]
        return None

    def get_print_settings_spec(self, print_settings_id, document_type=''):
        self.requested_print_settings_id = (
            print_settings_id,
            document_type,
        )
        if (
            print_settings_id == 'profile-1'
            and document_type == WORKSHEET_DOCUMENT_TYPE
        ):
            return self.print_profiles[0]
        return None

    def create_print_settings(self, params):
        self.created_params = params
        return 'created-profile'

    def update_print_settings(self, params):
        self.updated_params = params
        return self.update_exists


class GetPrintSettingsUseCaseTests(TestCase):
    def test_returns_list_filtered_by_document_type(self):
        repo = FakePrintSettingsRepository()

        data = GetPrintSettingsListUseCase(repo).execute(
            GetPrintSettingsListRequest(
                document_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertEqual(
            repo.requested_document_type,
            WORKSHEET_DOCUMENT_TYPE,
        )
        self.assertEqual(data.print_profiles[0].name, 'Рабочий лист')

    def test_returns_profile_by_clean_identifiers(self):
        repo = FakePrintSettingsRepository()

        data = GetPrintSettingsUseCase(repo).execute(
            GetPrintSettingsRequest(
                print_settings_id='profile-1',
                document_type=WORKSHEET_DOCUMENT_TYPE,
            )
        )

        self.assertEqual(data.print_profile.name, 'Рабочий лист')
        self.assertEqual(
            repo.requested_print_settings_id,
            ('profile-1', WORKSHEET_DOCUMENT_TYPE),
        )

    def test_returns_default_profile(self):
        repo = FakePrintSettingsRepository()

        data = GetDefaultPrintSettingsUseCase(repo).execute(
            GetDefaultPrintSettingsRequest(
                document_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertEqual(
            repo.default_document_type,
            WORKSHEET_DOCUMENT_TYPE,
        )
        self.assertEqual(data.print_profile.name, 'Рабочий лист')

    def test_returns_none_when_default_profile_is_missing(self):
        repo = FakePrintSettingsRepository()

        data = GetDefaultPrintSettingsUseCase(repo).execute(
            GetDefaultPrintSettingsRequest(
                document_type=ANSWER_KEY_DOCUMENT_TYPE,
            ),
        )

        self.assertIsNone(data.print_profile)


class PrintSettingsSelectionTests(TestCase):
    def test_request_spec_takes_precedence(self):
        repo = FakePrintSettingsRepository()
        request_spec = PrintSettingsSpec(
            name='Из запроса',
            document_type=WORKSHEET_DOCUMENT_TYPE,
        )

        print_settings = resolve_document_print_settings_spec(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            request_print_settings_spec=request_spec,
            print_settings_repo=repo,
        )

        self.assertEqual(print_settings, request_spec)
        self.assertIsNone(repo.default_document_type)

    def test_returns_profile_by_id(self):
        repo = FakePrintSettingsRepository()

        print_settings = resolve_document_print_settings_spec(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            request_print_settings_id='profile-1',
            print_settings_repo=repo,
        )

        self.assertEqual(print_settings.name, 'Рабочий лист')
        self.assertEqual(
            repo.requested_print_settings_id,
            ('profile-1', WORKSHEET_DOCUMENT_TYPE),
        )
        self.assertIsNone(repo.default_document_type)

    def test_returns_none_without_explicit_profile(self):
        repo = FakePrintSettingsRepository()

        print_settings = resolve_document_print_settings_spec(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            print_settings_repo=repo,
        )

        self.assertIsNone(print_settings)
        self.assertIsNone(repo.default_document_type)

    def test_returns_none_without_repository(self):
        print_settings = resolve_document_print_settings_spec(
            document_type=WORKSHEET_DOCUMENT_TYPE,
        )

        self.assertIsNone(print_settings)


class CreatePrintSettingsUseCaseTests(TestCase):
    def test_creates_profile_from_valid_params(self):
        repo = FakePrintSettingsRepository()
        params = CreatePrintSettingsParams(
            name='  Профиль работы  ',
            description='  Для печати  ',
            document_type='work',
            is_default=True,
        )

        result = CreatePrintSettingsUseCase(repo).execute(params)

        self.assertEqual(result.status, PRINT_SETTINGS_CREATE_STATUS_CREATED)
        self.assertEqual(result.print_settings_id, 'created-profile')
        self.assertEqual(repo.created_params.name, 'Профиль работы')
        self.assertEqual(repo.created_params.description, 'Для печати')
        self.assertTrue(repo.created_params.is_default)

    def test_rejects_missing_required_fields(self):
        repo = FakePrintSettingsRepository()

        result = CreatePrintSettingsUseCase(repo).execute(
            CreatePrintSettingsParams(
                name='',
                document_type='',
            )
        )

        self.assertEqual(result.status, PRINT_SETTINGS_CREATE_STATUS_INVALID)
        self.assertIn('Название профиля печати обязательно.', result.errors)
        self.assertIn('Тип документа обязателен.', result.errors)
        self.assertIsNone(repo.created_params)

    def test_rejects_unknown_document_type(self):
        repo = FakePrintSettingsRepository()

        result = CreatePrintSettingsUseCase(repo).execute(
            CreatePrintSettingsParams(
                name='Профиль РнО',
                document_type='unknown',
            )
        )

        self.assertEqual(result.status, PRINT_SETTINGS_CREATE_STATUS_INVALID)
        self.assertIn(
            'Unsupported document type: unknown',
            result.errors,
        )


class UpdatePrintSettingsUseCaseTests(TestCase):
    def test_updates_profile_from_valid_params(self):
        repo = FakePrintSettingsRepository()
        params = UpdatePrintSettingsParams(
            print_settings_id='profile-1',
            name='  Новый профиль  ',
            description='  Новое описание  ',
            document_type='work',
            is_default=True,
        )

        result = UpdatePrintSettingsUseCase(repo).execute(params)

        self.assertEqual(result.status, PRINT_SETTINGS_UPDATE_STATUS_UPDATED)
        self.assertEqual(result.print_settings_id, 'profile-1')
        self.assertEqual(repo.updated_params.name, 'Новый профиль')
        self.assertEqual(repo.updated_params.description, 'Новое описание')
        self.assertTrue(repo.updated_params.is_default)

    def test_returns_not_found_for_missing_profile(self):
        repo = FakePrintSettingsRepository()
        repo.update_exists = False

        result = UpdatePrintSettingsUseCase(repo).execute(
            UpdatePrintSettingsParams(
                print_settings_id='missing',
                name='Профиль',
                document_type='work',
            )
        )

        self.assertEqual(
            result.status,
            PRINT_SETTINGS_UPDATE_STATUS_NOT_FOUND,
        )

    def test_rejects_invalid_update(self):
        repo = FakePrintSettingsRepository()

        result = UpdatePrintSettingsUseCase(repo).execute(
            UpdatePrintSettingsParams(
                print_settings_id='profile-1',
                name='Профиль РнО',
                document_type='unknown',
            )
        )

        self.assertEqual(result.status, PRINT_SETTINGS_UPDATE_STATUS_INVALID)
        self.assertIsNone(repo.updated_params)
