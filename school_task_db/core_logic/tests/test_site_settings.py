from unittest import TestCase

from core_logic.entities.site_settings import (
    SaveSiteSettingsParams,
    SaveSiteSettingsResult,
    SiteSettingsData,
)
from core_logic.use_cases.get_site_settings import GetSiteSettingsUseCase
from core_logic.use_cases.save_site_settings import SaveSiteSettingsUseCase


class FakeSettingsRepository:
    def __init__(self):
        self.saved_params = None

    def get_site_settings(self):
        return SiteSettingsData(school_name='Лицей')

    def save_site_settings(self, params):
        self.saved_params = params
        return SaveSiteSettingsResult(status='saved')


class SiteSettingsUseCaseTests(TestCase):
    def test_get_site_settings_delegates_to_repository(self):
        result = GetSiteSettingsUseCase(FakeSettingsRepository()).execute()

        self.assertEqual(result.school_name, 'Лицей')

    def test_save_site_settings_delegates_to_repository(self):
        repo = FakeSettingsRepository()
        params = SaveSiteSettingsParams(
            school_name='Лицей',
            teacher_name='Иванова',
            default_subject='Физика',
            current_academic_year='2026-2027',
        )

        result = SaveSiteSettingsUseCase(repo).execute(params)

        self.assertEqual(result.status, 'saved')
        self.assertEqual(repo.saved_params, params)
