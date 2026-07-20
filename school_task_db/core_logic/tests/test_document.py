from unittest import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSection,
    DocumentSectionSpec,
    DocumentSourceRef,
    DocumentTemplateSpec,
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
        document = Document(title='Разбор', document_type='remedial_sheet')

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

    def test_template_spec_preserves_ordered_sections(self):
        template = DocumentTemplateSpec(
            name='Тренировочный лист',
            template_type='worksheet',
            sections=[
                DocumentSectionSpec(section_type='header'),
                DocumentSectionSpec(
                    section_type='task_list',
                    options={'source': 'new_tasks'},
                ),
            ],
            default_content_config={'answer_type': 'tasks_only'},
        )

        self.assertEqual(template.name, 'Тренировочный лист')
        self.assertEqual(template.template_type, 'worksheet')
        self.assertEqual(template.section_types, ('header', 'task_list'))
        self.assertEqual(
            template.default_content_config,
            {'answer_type': 'tasks_only'},
        )

    def test_template_spec_copies_default_content_config(self):
        default_content_config = {'answer_type': 'with_answers'}
        template = DocumentTemplateSpec(
            name='Ключ',
            template_type='answer_key',
            default_content_config=default_content_config,
        )

        default_content_config['answer_type'] = 'tasks_only'

        self.assertEqual(
            template.default_content_config,
            {'answer_type': 'with_answers'},
        )

    def test_template_spec_converts_to_recipe(self):
        template = DocumentTemplateSpec(
            name='Работа над ошибками',
            template_type='remedial_sheet',
            sections=[
                DocumentSectionSpec(section_type='header'),
                DocumentSectionSpec(section_type='answer_key'),
            ],
        )

        recipe = template.to_recipe()
        overridden_recipe = template.to_recipe(document_type='custom')

        self.assertEqual(recipe.document_type, 'remedial_sheet')
        self.assertEqual(recipe.section_types, ('header', 'answer_key'))
        self.assertEqual(overridden_recipe.document_type, 'custom')

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
            DocumentTemplateSpec(name='Invalid', template_type='')
