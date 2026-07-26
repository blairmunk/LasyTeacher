from django.test import TestCase

from core_logic.entities.document import (
    CreatePrintSettingsParams,
    DocumentPresentation,
    DocumentSectionSpec,
    PrintSettingsSpec,
    UpdatePrintSettingsParams,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from document_engine.models import PrintSettings
from infrastructure.repositories.django_print_settings_repo import (
    DjangoPrintSettingsRepository,
)


class DjangoPrintSettingsRepositoryTests(TestCase):
    def test_implements_clean_port(self):
        self.assertIsInstance(
            DjangoPrintSettingsRepository(),
            IPrintSettingsRepository,
        )

    def test_lists_profiles_filtered_by_document_type(self):
        PrintSettings.objects.create(
            name='Рабочий лист',
            document_type=PrintSettings.DocumentType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )
        PrintSettings.objects.create(
            name='Ключ',
            document_type=PrintSettings.DocumentType.ANSWER_KEY,
            sections_config=[{'type': 'answers'}],
        )

        profiles = DjangoPrintSettingsRepository().list_print_settings_specs(
            document_type=PrintSettings.DocumentType.WORKSHEET,
        )

        self.assertEqual(len(profiles), 1)
        self.assertIsInstance(profiles[0], PrintSettingsSpec)
        self.assertEqual(profiles[0].name, 'Рабочий лист')
        self.assertEqual(profiles[0].document_type, 'worksheet')
        self.assertEqual(profiles[0].section_types, ('header',))

    def test_returns_default_profile(self):
        PrintSettings.objects.create(
            name='Обычный профиль',
            document_type=PrintSettings.DocumentType.WORKSHEET,
            is_default=False,
            sections_config=[{'type': 'header'}],
        )
        PrintSettings.objects.create(
            name='Основной профиль',
            document_type=PrintSettings.DocumentType.WORKSHEET,
            is_default=True,
            sections_config=[{'type': 'task_list'}],
        )

        profile = (
            DjangoPrintSettingsRepository()
            .get_default_print_settings_spec(
                PrintSettings.DocumentType.WORKSHEET,
            )
        )

        self.assertEqual(profile.name, 'Основной профиль')
        self.assertEqual(profile.section_types, ('task_list',))

    def test_returns_none_when_default_profile_missing(self):
        profile = (
            DjangoPrintSettingsRepository()
            .get_default_print_settings_spec(
                PrintSettings.DocumentType.WORKSHEET,
            )
        )

        self.assertIsNone(profile)

    def test_returns_profile_by_id_and_type(self):
        model = PrintSettings.objects.create(
            name='Рабочий лист',
            document_type=PrintSettings.DocumentType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )

        profile = DjangoPrintSettingsRepository().get_print_settings_spec(
            print_settings_id=str(model.pk),
            document_type=PrintSettings.DocumentType.WORKSHEET,
        )

        self.assertEqual(profile.print_settings_id, str(model.pk))
        self.assertEqual(profile.name, 'Рабочий лист')

    def test_returns_none_when_profile_has_wrong_type(self):
        model = PrintSettings.objects.create(
            name='Рабочий лист',
            document_type=PrintSettings.DocumentType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )

        profile = DjangoPrintSettingsRepository().get_print_settings_spec(
            print_settings_id=str(model.pk),
            document_type=PrintSettings.DocumentType.ANSWER_KEY,
        )

        self.assertIsNone(profile)

    def test_creates_profile_preserving_section_specs(self):
        profile_id = DjangoPrintSettingsRepository().create_print_settings(
            CreatePrintSettingsParams(
                name='Рабочий лист',
                document_type=PrintSettings.DocumentType.WORK,
                sections=(
                    DocumentSectionSpec(section_type='header'),
                    DocumentSectionSpec(
                        section_type='blank_cells',
                        title='Черновик',
                        options={'rows': 8},
                    ),
                    DocumentSectionSpec(section_type='page_break'),
                ),
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
        self.assertEqual(
            model.sections_config,
            [
                {'type': 'header'},
                {
                    'type': 'blank_cells',
                    'title': 'Черновик',
                    'params': {'rows': 8},
                },
                {'type': 'page_break'},
            ],
        )
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
            sections_config=[{'type': 'header'}],
            is_default=True,
        )

        DjangoPrintSettingsRepository().create_print_settings(
            CreatePrintSettingsParams(
                name='Новый профиль',
                document_type=PrintSettings.DocumentType.WORK,
                section_types=('header', 'task_list'),
                is_default=True,
            )
        )

        old_default.refresh_from_db()
        self.assertFalse(old_default.is_default)

    def test_updates_profile_preserving_section_specs(self):
        model = PrintSettings.objects.create(
            name='Старый профиль',
            document_type=PrintSettings.DocumentType.WORK,
            sections_config=[{'type': 'header'}],
        )

        updated = DjangoPrintSettingsRepository().update_print_settings(
            UpdatePrintSettingsParams(
                print_settings_id=str(model.pk),
                name='Новый профиль',
                description='Новое описание',
                document_type=PrintSettings.DocumentType.WORK,
                sections=(
                    DocumentSectionSpec(section_type='page_break'),
                    DocumentSectionSpec(
                        section_type='blank_cells',
                        options={'rows': 5},
                    ),
                ),
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
        self.assertEqual(
            model.sections_config,
            [
                {'type': 'page_break'},
                {'type': 'blank_cells', 'params': {'rows': 5}},
            ],
        )
        self.assertTrue(model.is_default)
        self.assertEqual(model.custom_css, '.task { margin: 1rem; }')
        self.assertEqual(
            model.custom_latex_preamble,
            '\\usepackage{geometry}',
        )
        self.assertEqual(
            model.html_template_override,
            '<article>{{ body_content }}</article>',
        )
        self.assertEqual(
            model.latex_template_override,
            '\\section*{Лист}{{ body_content }}',
        )

    def test_update_returns_false_for_missing_profile(self):
        updated = DjangoPrintSettingsRepository().update_print_settings(
            UpdatePrintSettingsParams(
                print_settings_id='550e8400-e29b-41d4-a716-446655440000',
                name='Профиль',
                document_type=PrintSettings.DocumentType.WORK,
                section_types=('header',),
            )
        )

        self.assertFalse(updated)
