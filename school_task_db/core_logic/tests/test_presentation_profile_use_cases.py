from unittest import TestCase

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    DocumentPresentationProfile,
    UpdatePresentationProfileParams,
)
from core_logic.use_cases.create_presentation_profile import (
    PRESENTATION_PROFILE_CREATE_STATUS_CREATED,
    PRESENTATION_PROFILE_CREATE_STATUS_INVALID,
    CreatePresentationProfileUseCase,
)
from core_logic.use_cases.get_presentation_profile import (
    GetPresentationProfileRequest,
    GetPresentationProfileUseCase,
)
from core_logic.use_cases.get_presentation_profile_list import (
    GetPresentationProfileListRequest,
    GetPresentationProfileListUseCase,
)
from core_logic.use_cases.presentation_profile_selection import (
    resolve_document_presentation_profile,
)
from core_logic.use_cases.update_presentation_profile import (
    PRESENTATION_PROFILE_UPDATE_STATUS_INVALID,
    PRESENTATION_PROFILE_UPDATE_STATUS_NOT_FOUND,
    PRESENTATION_PROFILE_UPDATE_STATUS_UPDATED,
    UpdatePresentationProfileUseCase,
)
from core_logic.value_objects.document_recipes import (
    WORKSHEET_DOCUMENT_TYPE,
)


class FakePresentationProfileRepository:
    def __init__(self):
        self.requested_document_type = None
        self.requested_presentation_profile_id = None
        self.created_params = None
        self.updated_params = None
        self.update_exists = True
        self.presentation_profiles = [
            DocumentPresentationProfile(
                name='Рабочий лист',
                document_type=WORKSHEET_DOCUMENT_TYPE,
                presentation_profile_id='profile-1',
            )
        ]

    def list_presentation_profiles(self, document_type=''):
        self.requested_document_type = document_type
        return self.presentation_profiles

    def get_presentation_profile(self, presentation_profile_id, document_type=''):
        self.requested_presentation_profile_id = (
            presentation_profile_id,
            document_type,
        )
        if (
            presentation_profile_id == 'profile-1'
            and document_type == WORKSHEET_DOCUMENT_TYPE
        ):
            return self.presentation_profiles[0]
        return None

    def create_presentation_profile(self, params):
        self.created_params = params
        return 'created-profile'

    def update_presentation_profile(self, params):
        self.updated_params = params
        return self.update_exists


class GetPresentationProfileUseCaseTests(TestCase):
    def test_returns_list_filtered_by_document_type(self):
        repo = FakePresentationProfileRepository()

        data = GetPresentationProfileListUseCase(repo).execute(
            GetPresentationProfileListRequest(
                document_type=WORKSHEET_DOCUMENT_TYPE,
            ),
        )

        self.assertEqual(
            repo.requested_document_type,
            WORKSHEET_DOCUMENT_TYPE,
        )
        self.assertEqual(data.presentation_profiles[0].name, 'Рабочий лист')

    def test_returns_profile_by_clean_identifiers(self):
        repo = FakePresentationProfileRepository()

        data = GetPresentationProfileUseCase(repo).execute(
            GetPresentationProfileRequest(
                presentation_profile_id='profile-1',
                document_type=WORKSHEET_DOCUMENT_TYPE,
            )
        )

        self.assertEqual(data.presentation_profile.name, 'Рабочий лист')
        self.assertEqual(
            repo.requested_presentation_profile_id,
            ('profile-1', WORKSHEET_DOCUMENT_TYPE),
        )

class PresentationProfileSelectionTests(TestCase):
    def test_request_spec_takes_precedence(self):
        repo = FakePresentationProfileRepository()
        request_spec = DocumentPresentationProfile(
            name='Из запроса',
            document_type=WORKSHEET_DOCUMENT_TYPE,
        )

        selected_profile = resolve_document_presentation_profile(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            request_presentation_profile=request_spec,
            presentation_profile_repo=repo,
        )

        self.assertEqual(selected_profile, request_spec)

    def test_rejects_request_profile_for_another_document_type(self):
        request_spec = DocumentPresentationProfile(
            name='Чужой профиль',
            document_type='event_performance_report',
        )

        selected_profile = resolve_document_presentation_profile(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            request_presentation_profile=request_spec,
        )

        self.assertIsNone(selected_profile)

    def test_returns_profile_by_id(self):
        repo = FakePresentationProfileRepository()

        selected_profile = resolve_document_presentation_profile(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            request_presentation_profile_id='profile-1',
            presentation_profile_repo=repo,
        )

        self.assertEqual(selected_profile.name, 'Рабочий лист')
        self.assertEqual(
            repo.requested_presentation_profile_id,
            ('profile-1', WORKSHEET_DOCUMENT_TYPE),
        )

    def test_returns_none_without_explicit_profile(self):
        repo = FakePresentationProfileRepository()

        selected_profile = resolve_document_presentation_profile(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            presentation_profile_repo=repo,
        )

        self.assertIsNone(selected_profile)

    def test_returns_none_without_repository(self):
        selected_profile = resolve_document_presentation_profile(
            document_type=WORKSHEET_DOCUMENT_TYPE,
        )

        self.assertIsNone(selected_profile)


class CreatePresentationProfileUseCaseTests(TestCase):
    def test_creates_profile_from_valid_params(self):
        repo = FakePresentationProfileRepository()
        params = CreatePresentationProfileParams(
            name='  Профиль работы  ',
            description='  Для печати  ',
            document_type='work',
            is_default=True,
        )

        result = CreatePresentationProfileUseCase(repo).execute(params)

        self.assertEqual(result.status, PRESENTATION_PROFILE_CREATE_STATUS_CREATED)
        self.assertEqual(result.presentation_profile_id, 'created-profile')
        self.assertEqual(repo.created_params.name, 'Профиль работы')
        self.assertEqual(repo.created_params.description, 'Для печати')
        self.assertTrue(repo.created_params.is_default)

    def test_rejects_missing_required_fields(self):
        repo = FakePresentationProfileRepository()

        result = CreatePresentationProfileUseCase(repo).execute(
            CreatePresentationProfileParams(
                name='',
                document_type='',
            )
        )

        self.assertEqual(result.status, PRESENTATION_PROFILE_CREATE_STATUS_INVALID)
        self.assertIn('Название профиля печати обязательно.', result.errors)
        self.assertIn('Тип документа обязателен.', result.errors)
        self.assertIsNone(repo.created_params)

    def test_rejects_unknown_document_type(self):
        repo = FakePresentationProfileRepository()

        result = CreatePresentationProfileUseCase(repo).execute(
            CreatePresentationProfileParams(
                name='Профиль РнО',
                document_type='unknown',
            )
        )

        self.assertEqual(result.status, PRESENTATION_PROFILE_CREATE_STATUS_INVALID)
        self.assertIn(
            'Unsupported document type: unknown',
            result.errors,
        )


class UpdatePresentationProfileUseCaseTests(TestCase):
    def test_updates_profile_from_valid_params(self):
        repo = FakePresentationProfileRepository()
        params = UpdatePresentationProfileParams(
            presentation_profile_id='profile-1',
            name='  Новый профиль  ',
            description='  Новое описание  ',
            document_type='work',
            is_default=True,
        )

        result = UpdatePresentationProfileUseCase(repo).execute(params)

        self.assertEqual(result.status, PRESENTATION_PROFILE_UPDATE_STATUS_UPDATED)
        self.assertEqual(result.presentation_profile_id, 'profile-1')
        self.assertEqual(repo.updated_params.name, 'Новый профиль')
        self.assertEqual(repo.updated_params.description, 'Новое описание')
        self.assertTrue(repo.updated_params.is_default)

    def test_returns_not_found_for_missing_profile(self):
        repo = FakePresentationProfileRepository()
        repo.update_exists = False

        result = UpdatePresentationProfileUseCase(repo).execute(
            UpdatePresentationProfileParams(
                presentation_profile_id='missing',
                name='Профиль',
                document_type='work',
            )
        )

        self.assertEqual(
            result.status,
            PRESENTATION_PROFILE_UPDATE_STATUS_NOT_FOUND,
        )

    def test_rejects_invalid_update(self):
        repo = FakePresentationProfileRepository()

        result = UpdatePresentationProfileUseCase(repo).execute(
            UpdatePresentationProfileParams(
                presentation_profile_id='profile-1',
                name='Профиль РнО',
                document_type='unknown',
            )
        )

        self.assertEqual(result.status, PRESENTATION_PROFILE_UPDATE_STATUS_INVALID)
        self.assertIsNone(repo.updated_params)
