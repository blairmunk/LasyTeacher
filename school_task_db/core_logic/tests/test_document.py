from unittest import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSection,
    DocumentSectionSpec,
    DocumentSourceRef,
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

    def test_rejects_empty_required_identifiers(self):
        with self.assertRaises(ValueError):
            DocumentSourceRef(source_type='')
        with self.assertRaises(ValueError):
            DocumentSection(section_type='')
        with self.assertRaises(ValueError):
            DocumentSectionSpec(section_type='')
        with self.assertRaises(ValueError):
            DocumentRecipe(document_type='')
