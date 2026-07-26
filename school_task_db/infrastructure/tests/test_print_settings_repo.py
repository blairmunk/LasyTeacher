from django.test import TestCase

from core_logic.entities.document import (
    CreatePrintSettingsParams,
    DocumentSectionSpec,
    PrintSettingsSpec,
    UpdatePrintSettingsParams,
)
from core_logic.interfaces.print_settings_repo import (
    IPrintSettingsRepository,
)
from document_generator.models import DocumentTemplate
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
        DocumentTemplate.objects.create(
            name='Рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )
        DocumentTemplate.objects.create(
            name='Ключ',
            template_type=DocumentTemplate.TemplateType.ANSWER_KEY,
            sections_config=[{'type': 'answers'}],
        )

        profiles = DjangoPrintSettingsRepository().list_print_settings_specs(
            document_type=DocumentTemplate.TemplateType.WORKSHEET,
        )

        self.assertEqual(len(profiles), 1)
        self.assertIsInstance(profiles[0], PrintSettingsSpec)
        self.assertEqual(profiles[0].name, 'Рабочий лист')
        self.assertEqual(profiles[0].document_type, 'worksheet')
        self.assertEqual(profiles[0].section_types, ('header',))

    def test_returns_default_profile(self):
        DocumentTemplate.objects.create(
            name='Обычный профиль',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            is_default=False,
            sections_config=[{'type': 'header'}],
        )
        DocumentTemplate.objects.create(
            name='Основной профиль',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            is_default=True,
            sections_config=[{'type': 'task_list'}],
        )

        profile = (
            DjangoPrintSettingsRepository()
            .get_default_print_settings_spec(
                DocumentTemplate.TemplateType.WORKSHEET,
            )
        )

        self.assertEqual(profile.name, 'Основной профиль')
        self.assertEqual(profile.section_types, ('task_list',))

    def test_returns_none_when_default_profile_missing(self):
        profile = (
            DjangoPrintSettingsRepository()
            .get_default_print_settings_spec(
                DocumentTemplate.TemplateType.WORKSHEET,
            )
        )

        self.assertIsNone(profile)

    def test_returns_profile_by_id_and_type(self):
        model = DocumentTemplate.objects.create(
            name='Рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )

        profile = DjangoPrintSettingsRepository().get_print_settings_spec(
            print_settings_id=str(model.pk),
            document_type=DocumentTemplate.TemplateType.WORKSHEET,
        )

        self.assertEqual(profile.print_settings_id, str(model.pk))
        self.assertEqual(profile.name, 'Рабочий лист')

    def test_returns_none_when_profile_has_wrong_type(self):
        model = DocumentTemplate.objects.create(
            name='Рабочий лист',
            template_type=DocumentTemplate.TemplateType.WORKSHEET,
            sections_config=[{'type': 'header'}],
        )

        profile = DjangoPrintSettingsRepository().get_print_settings_spec(
            print_settings_id=str(model.pk),
            document_type=DocumentTemplate.TemplateType.ANSWER_KEY,
        )

        self.assertIsNone(profile)

    def test_creates_profile_preserving_section_specs(self):
        profile_id = DjangoPrintSettingsRepository().create_print_settings(
            CreatePrintSettingsParams(
                name='Рабочий лист',
                document_type=DocumentTemplate.TemplateType.WORK,
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
            )
        )

        model = DocumentTemplate.objects.get(pk=profile_id)
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

    def test_creating_default_profile_clears_previous_default(self):
        old_default = DocumentTemplate.objects.create(
            name='Старый профиль',
            template_type=DocumentTemplate.TemplateType.WORK,
            sections_config=[{'type': 'header'}],
            is_default=True,
        )

        DjangoPrintSettingsRepository().create_print_settings(
            CreatePrintSettingsParams(
                name='Новый профиль',
                document_type=DocumentTemplate.TemplateType.WORK,
                section_types=('header', 'task_list'),
                is_default=True,
            )
        )

        old_default.refresh_from_db()
        self.assertFalse(old_default.is_default)

    def test_updates_profile_preserving_section_specs(self):
        model = DocumentTemplate.objects.create(
            name='Старый профиль',
            template_type=DocumentTemplate.TemplateType.WORK,
            sections_config=[{'type': 'header'}],
        )

        updated = DjangoPrintSettingsRepository().update_print_settings(
            UpdatePrintSettingsParams(
                print_settings_id=str(model.pk),
                name='Новый профиль',
                description='Новое описание',
                document_type=DocumentTemplate.TemplateType.WORK,
                sections=(
                    DocumentSectionSpec(section_type='page_break'),
                    DocumentSectionSpec(
                        section_type='blank_cells',
                        options={'rows': 5},
                    ),
                ),
                is_default=True,
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

    def test_update_returns_false_for_missing_profile(self):
        updated = DjangoPrintSettingsRepository().update_print_settings(
            UpdatePrintSettingsParams(
                print_settings_id='550e8400-e29b-41d4-a716-446655440000',
                name='Профиль',
                document_type=DocumentTemplate.TemplateType.WORK,
                section_types=('header',),
            )
        )

        self.assertFalse(updated)
