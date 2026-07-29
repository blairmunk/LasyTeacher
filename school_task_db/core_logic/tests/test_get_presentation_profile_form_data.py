from unittest import TestCase

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.use_cases.get_presentation_profile_form_data import (
    GetPresentationProfileFormDataRequest,
    GetPresentationProfileFormDataUseCase,
)
from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)


class FakePresentationProfileRepository:
    def __init__(self, presentation_profile=None):
        self.presentation_profile = presentation_profile
        self.presentation_profile_id = None

    def get_presentation_profile(self, presentation_profile_id, document_type=''):
        self.presentation_profile_id = presentation_profile_id
        return self.presentation_profile


class GetPresentationProfileFormDataUseCaseTests(TestCase):
    def test_returns_renderable_types_for_create_form(self):
        data = GetPresentationProfileFormDataUseCase().execute()

        self.assertEqual(
            [item.document_type for item in data.document_types],
            [WORK_DOCUMENT_TYPE, REMEDIAL_SHEET_DOCUMENT_TYPE],
        )
        self.assertIsNone(data.presentation_profile)

    def test_loads_profile_for_update_form(self):
        presentation_profile = DocumentPresentationProfile(
            presentation_profile_id='profile-1',
            name='Профиль',
            document_type=WORK_DOCUMENT_TYPE,
        )
        repo = FakePresentationProfileRepository(presentation_profile=presentation_profile)

        data = GetPresentationProfileFormDataUseCase(repo).execute(
            GetPresentationProfileFormDataRequest(
                presentation_profile_id='profile-1',
            ),
        )

        self.assertEqual(repo.presentation_profile_id, 'profile-1')
        self.assertEqual(data.presentation_profile, presentation_profile)
