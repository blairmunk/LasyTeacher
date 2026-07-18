from django.test import TestCase
from django.urls import reverse

from core_logic.entities.site_settings import SaveSiteSettingsParams
from infrastructure.repositories.django_settings_repo import DjangoSettingsRepository
from site_settings.models import SiteSettings


class SiteSettingsViewTests(TestCase):
    def test_get_creates_singleton_settings_context(self):
        response = self.client.get(reverse('site_settings:index'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['object'].default_subject, 'Физика')
        self.assertEqual(
            response.context['form'].initial['default_subject'],
            'Физика',
        )

    def test_post_updates_settings(self):
        response = self.client.post(
            reverse('site_settings:index'),
            data={
                'school_name': 'Лицей',
                'teacher_name': 'Иванова М. И.',
                'default_subject': 'Физика',
                'current_academic_year': '2026-2027',
                'points_scale': 100,
                'default_variants_count': 4,
                'pdf_font_size': 12,
                'pdf_margin_top': 15,
                'pdf_margin_bottom': 15,
            },
        )

        settings = SiteSettings.get()
        self.assertRedirects(
            response,
            reverse('site_settings:index'),
            fetch_redirect_response=False,
        )
        self.assertEqual(settings.school_name, 'Лицей')
        self.assertEqual(settings.default_variants_count, 4)


class DjangoSettingsRepositoryTests(TestCase):
    def test_returns_and_saves_singleton_settings(self):
        repo = DjangoSettingsRepository()

        result = repo.save_site_settings(
            SaveSiteSettingsParams(
                school_name='Гимназия',
                teacher_name='Петрова',
                default_subject='Математика',
                current_academic_year='2026-2027',
                points_scale=50,
                default_variants_count=3,
                pdf_font_size=11,
                pdf_margin_top=12,
                pdf_margin_bottom=13,
            )
        )
        settings = repo.get_site_settings()

        self.assertEqual(result.status, 'saved')
        self.assertEqual(settings.school_name, 'Гимназия')
        self.assertEqual(settings.default_subject, 'Математика')
        self.assertEqual(settings.default_variants_count, 3)
        self.assertEqual(settings.pdf_margin_bottom, 13)
