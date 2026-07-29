from django.test import TestCase

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    DocumentPresentation,
    DocumentPresentationProfile,
    UpdatePresentationProfileParams,
)
from core_logic.interfaces.presentation_profile_repo import IPresentationProfileRepository
from document_engine.models import PrintSettings
from infrastructure.repositories.django_presentation_profile_repo import (
    DjangoPresentationProfileRepository,
)


class DjangoPresentationProfileRepositoryTests(TestCase):
    def test_implements_clean_port(self):
        self.assertIsInstance(
            DjangoPresentationProfileRepository(),
            IPresentationProfileRepository,
        )

    def test_lists_profiles_filtered_by_document_type(self):
        PrintSettings.objects.create(
            name='Рабочий лист',
            document_type=PrintSettings.DocumentType.WORKSHEET,
        )
        PrintSettings.objects.create(
            name='Ключ',
            document_type=PrintSettings.DocumentType.ANSWER_KEY,
        )

        profiles = DjangoPresentationProfileRepository().list_presentation_profiles(
            document_type=PrintSettings.DocumentType.WORKSHEET,
        )

        self.assertEqual(len(profiles), 1)
        self.assertIsInstance(profiles[0], DocumentPresentationProfile)
        self.assertEqual(profiles[0].name, 'Рабочий лист')
        self.assertEqual(profiles[0].document_type, 'worksheet')

    def test_returns_profile_by_id_and_type(self):
        model = PrintSettings.objects.create(
            name='Рабочий лист',
            document_type=PrintSettings.DocumentType.WORKSHEET,
        )

        profile = DjangoPresentationProfileRepository().get_presentation_profile(
            presentation_profile_id=str(model.pk),
            document_type=PrintSettings.DocumentType.WORKSHEET,
        )

        self.assertEqual(profile.presentation_profile_id, str(model.pk))
        self.assertEqual(profile.name, 'Рабочий лист')

    def test_returns_none_when_profile_has_wrong_type(self):
        model = PrintSettings.objects.create(
            name='Рабочий лист',
            document_type=PrintSettings.DocumentType.WORKSHEET,
        )

        profile = DjangoPresentationProfileRepository().get_presentation_profile(
            presentation_profile_id=str(model.pk),
            document_type=PrintSettings.DocumentType.ANSWER_KEY,
        )

        self.assertIsNone(profile)

    def test_creates_profile_preserving_presentation(self):
        profile_id = DjangoPresentationProfileRepository().create_presentation_profile(
            CreatePresentationProfileParams(
                name='Рабочий лист',
                document_type=PrintSettings.DocumentType.WORK,
                is_default=True,
                presentation=DocumentPresentation(
                    custom_css='body { font-size: 12pt; }',
                    custom_latex_preamble='\\usepackage{multicol}',
                    html_template_override='<main>{{ body_content }}</main>',
                    latex_template_override='\\begin{document}{{ body_content }}',
                ),
            )
        )

        model = PrintSettings.objects.get(pk=profile_id)
        self.assertTrue(model.is_default)
        self.assertEqual(model.custom_css, 'body { font-size: 12pt; }')
        self.assertEqual(
            model.custom_latex_preamble,
            '\\usepackage{multicol}',
        )
        self.assertEqual(
            model.html_template_override,
            '<main>{{ body_content }}</main>',
        )
        self.assertEqual(
            model.latex_template_override,
            '\\begin{document}{{ body_content }}',
        )

    def test_creating_default_profile_clears_previous_default(self):
        old_default = PrintSettings.objects.create(
            name='Старый профиль',
            document_type=PrintSettings.DocumentType.WORK,
            is_default=True,
        )

        DjangoPresentationProfileRepository().create_presentation_profile(
            CreatePresentationProfileParams(
                name='Новый профиль',
                document_type=PrintSettings.DocumentType.WORK,
                is_default=True,
            )
        )

        old_default.refresh_from_db()
        self.assertFalse(old_default.is_default)

    def test_updates_profile_preserving_presentation(self):
        model = PrintSettings.objects.create(
            name='Старый профиль',
            document_type=PrintSettings.DocumentType.WORK,
        )

        updated = DjangoPresentationProfileRepository().update_presentation_profile(
            UpdatePresentationProfileParams(
                presentation_profile_id=str(model.pk),
                name='Новый профиль',
                description='Новое описание',
                document_type=PrintSettings.DocumentType.WORK,
                is_default=True,
                presentation=DocumentPresentation(
                    custom_css='.task { margin: 1rem; }',
                    custom_latex_preamble='\\usepackage{geometry}',
                    html_template_override='<article>{{ body_content }}</article>',
                    latex_template_override='\\section*{Лист}{{ body_content }}',
                ),
            )
        )

        model.refresh_from_db()
        self.assertTrue(updated)
        self.assertEqual(model.name, 'Новый профиль')
        self.assertEqual(model.description, 'Новое описание')
        self.assertTrue(model.is_default)
        self.assertEqual(model.custom_css, '.task { margin: 1rem; }')
        self.assertEqual(
            model.custom_latex_preamble,
            '\\usepackage{geometry}',
        )

    def test_update_returns_false_for_missing_profile(self):
        updated = DjangoPresentationProfileRepository().update_presentation_profile(
            UpdatePresentationProfileParams(
                presentation_profile_id='550e8400-e29b-41d4-a716-446655440000',
                name='Профиль',
                document_type=PrintSettings.DocumentType.WORK,
            )
        )

        self.assertFalse(updated)
