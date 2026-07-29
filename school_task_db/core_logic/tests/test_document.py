from unittest import TestCase

from core_logic.entities.document import (
    CreatePresentationProfileParams,
    Document,
    DocumentPresentation,
    DocumentRecipe,
    DocumentSection,
    DocumentSectionSpec,
    DocumentSourceRef,
    DocumentPresentationProfile,
    UpdatePresentationProfileParams,
)
from core_logic.value_objects.document_recipes import (
    CUSTOM_DOCUMENT_TYPE,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)


class DocumentModelTests(TestCase):
    def test_document_preserves_ordered_sections(self):
        document = Document(
            title='Контрольная работа',
            document_type='work',
            source=DocumentSourceRef(
                source_type='work',
                source_id='work-1',
                title='Контрольная работа',
            ),
            sections=[
                DocumentSection(section_type='instructions'),
                DocumentSection(section_type='tasks'),
                DocumentSection(section_type='answers'),
            ],
        )

        self.assertEqual(
            document.section_types,
            ('instructions', 'tasks', 'answers'),
        )
        self.assertEqual(document.source.source_type, 'work')
        self.assertEqual(document.source.source_id, 'work-1')
        self.assertEqual(document.document_type, 'work')

    def test_document_can_be_extended_without_mutating_original(self):
        presentation = DocumentPresentation(
            custom_css='.task { margin: 1rem; }',
        )
        document = Document(
            title='Разбор',
            document_type='remedial_sheet',
            presentation=presentation,
        )

        updated_document = document.with_section(
            DocumentSection(
                section_type='remedial_tasks',
                payload={'task_ids': ['task-1']},
            )
        )

        self.assertEqual(document.section_types, ())
        self.assertEqual(updated_document.document_type, 'remedial_sheet')
        self.assertEqual(updated_document.section_types, ('remedial_tasks',))
        self.assertEqual(
            updated_document.sections[0].payload,
            {'task_ids': ['task-1']},
        )
        self.assertEqual(updated_document.presentation, presentation)

    def test_document_finds_sections_by_type(self):
        document = Document(
            title='Контрольная работа',
            sections=[
                DocumentSection(section_type='header'),
                DocumentSection(
                    section_type='task_list',
                    payload={'source': 'variant-1'},
                ),
                DocumentSection(
                    section_type='task_list',
                    payload={'source': 'variant-2'},
                ),
            ],
        )

        self.assertTrue(document.has_section('task_list'))
        self.assertFalse(document.has_section('answers'))
        self.assertEqual(
            tuple(
                section.payload['source']
                for section in document.sections_by_type('task_list')
            ),
            ('variant-1', 'variant-2'),
        )
        self.assertEqual(
            document.first_section('task_list').payload,
            {'source': 'variant-1'},
        )
        self.assertIsNone(document.first_section('answers'))

    def test_recipe_preserves_ordered_section_specs(self):
        recipe = DocumentRecipe(
            document_type='work',
            sections=[
                DocumentSectionSpec(
                    section_type='tasks',
                    title='Задания',
                    options={'include_hints': True},
                ),
                DocumentSectionSpec(
                    section_type='solutions',
                    options={'level': 'short'},
                ),
            ],
        )

        self.assertEqual(recipe.document_type, 'work')
        self.assertEqual(recipe.section_types, ('tasks', 'solutions'))
        self.assertEqual(recipe.sections[0].title, 'Задания')
        self.assertEqual(recipe.sections[0].options, {'include_hints': True})

    def test_recipe_can_be_extended_without_mutating_original(self):
        recipe = DocumentRecipe(document_type='remedial_sheet')

        updated_recipe = recipe.with_section(
            DocumentSectionSpec(
                section_type='original_mistakes',
                options={'include_scores': True},
            )
        )

        self.assertEqual(recipe.section_types, ())
        self.assertEqual(
            updated_recipe.section_types,
            ('original_mistakes',),
        )

    def test_recipe_finds_sections_by_type(self):
        recipe = DocumentRecipe(
            document_type='work',
            sections=[
                DocumentSectionSpec(section_type='header'),
                DocumentSectionSpec(
                    section_type='task_list',
                    options={'source': 'variant-1'},
                ),
                DocumentSectionSpec(
                    section_type='task_list',
                    options={'source': 'variant-2'},
                ),
            ],
        )

        self.assertTrue(recipe.has_section('task_list'))
        self.assertFalse(recipe.has_section('answers'))
        self.assertEqual(
            tuple(
                section.options['source']
                for section in recipe.sections_by_type('task_list')
            ),
            ('variant-1', 'variant-2'),
        )
        self.assertEqual(
            recipe.first_section('task_list').options,
            {'source': 'variant-1'},
        )
        self.assertIsNone(recipe.first_section('answers'))

    def test_presentation_profile_preserves_presentation(self):
        presentation = DocumentPresentation(custom_css='body {}')
        presentation_profile = DocumentPresentationProfile(
            name='Тренировочный лист',
            document_type=WORKSHEET_DOCUMENT_TYPE,
            presentation=presentation,
        )

        self.assertEqual(presentation_profile.name, 'Тренировочный лист')
        self.assertEqual(
            presentation_profile.document_type,
            WORKSHEET_DOCUMENT_TYPE,
        )
        self.assertEqual(presentation_profile.presentation, presentation)

    def test_presentation_profile_preserves_identity(self):
        presentation_profile = DocumentPresentationProfile(
            name='Профиль печати',
            document_type=WORKSHEET_DOCUMENT_TYPE,
            presentation_profile_id='profile-1',
        )

        self.assertEqual(presentation_profile.presentation_profile_id, 'profile-1')
        self.assertEqual(presentation_profile.document_type, WORKSHEET_DOCUMENT_TYPE)

    def test_create_presentation_profile_params_normalize_values(self):
        params = CreatePresentationProfileParams(
            name=' Шаблон ',
            document_type=' work ',
        )

        self.assertEqual(params.name, 'Шаблон')
        self.assertEqual(params.document_type, 'work')

    def test_presentation_profile_params_preserve_clean_identifiers(self):
        create_params = CreatePresentationProfileParams(
            name='Профиль печати',
            document_type='work',
            presentation=DocumentPresentation(custom_css='body {}'),
        )
        update_params = UpdatePresentationProfileParams(
            presentation_profile_id='profile-1',
            name='Профиль печати',
            document_type='work',
        )

        self.assertEqual(create_params.document_type, 'work')
        self.assertEqual(create_params.presentation.custom_css, 'body {}')
        self.assertEqual(update_params.document_type, 'work')
        self.assertEqual(update_params.presentation_profile_id, 'profile-1')

    def test_update_presentation_profile_params_normalize_identifier(self):
        params = UpdatePresentationProfileParams(
            presentation_profile_id=' template-1 ',
            name='Шаблон',
            document_type='work',
        )

        self.assertEqual(params.presentation_profile_id, 'template-1')

    def test_rejects_empty_required_identifiers(self):
        with self.assertRaises(ValueError):
            DocumentSourceRef(source_type='')
        with self.assertRaises(ValueError):
            DocumentSection(section_type='')
        with self.assertRaises(ValueError):
            DocumentSectionSpec(section_type='')
        with self.assertRaises(ValueError):
            DocumentRecipe(document_type='')
        with self.assertRaises(ValueError):
            DocumentPresentationProfile(name='Invalid', document_type='')
