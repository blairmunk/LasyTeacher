from unittest import TestCase

from core_logic.entities.document import PrintSettingsSpec
from core_logic.use_cases.get_print_settings_form_data import (
    GetPrintSettingsFormDataRequest,
    GetPrintSettingsFormDataUseCase,
)
from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)


class FakePrintSettingsRepository:
    def __init__(self, print_profile=None):
        self.print_profile = print_profile
        self.print_settings_id = None

    def get_print_settings_spec(self, print_settings_id, document_type=''):
        self.print_settings_id = print_settings_id
        return self.print_profile


class GetPrintSettingsFormDataUseCaseTests(TestCase):
    def test_returns_renderable_types_for_create_form(self):
        data = GetPrintSettingsFormDataUseCase().execute()

        self.assertEqual(
            [item.document_type for item in data.document_types],
            [WORK_DOCUMENT_TYPE, REMEDIAL_SHEET_DOCUMENT_TYPE],
        )
        self.assertIsNone(data.print_profile)

    def test_loads_profile_for_update_form(self):
        print_profile = PrintSettingsSpec(
            print_settings_id='profile-1',
            name='Профиль',
            document_type=WORK_DOCUMENT_TYPE,
        )
        repo = FakePrintSettingsRepository(print_profile=print_profile)

        data = GetPrintSettingsFormDataUseCase(repo).execute(
            GetPrintSettingsFormDataRequest(
                print_settings_id='profile-1',
            ),
        )

        self.assertEqual(repo.print_settings_id, 'profile-1')
        self.assertEqual(data.print_profile, print_profile)
