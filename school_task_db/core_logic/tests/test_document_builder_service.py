from unittest import TestCase

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
)
from core_logic.services.document_builder import RecipeDocumentBuilder


class RecipeDocumentBuilderTests(TestCase):
    def test_builds_document_from_source_and_recipe(self):
        builder = RecipeDocumentBuilder()
        source = DocumentSourceRef(
            source_type='work',
            source_id='work-1',
            title='Контрольная',
        )
        recipe = DocumentRecipe(
            document_type='work',
            sections=[
                DocumentSectionSpec(
                    section_type='tasks',
                    title='Задания',
                    options={'include_hints': True},
                ),
                DocumentSectionSpec(section_type='answers'),
            ],
        )

        document = builder.build(source, recipe)

        self.assertEqual(document.title, 'Контрольная')
        self.assertEqual(document.document_type, 'work')
        self.assertEqual(document.source, source)
        self.assertEqual(document.section_types, ('tasks', 'answers'))
        self.assertEqual(document.sections[0].title, 'Задания')
        self.assertEqual(document.sections[0].payload, {'include_hints': True})

    def test_copies_section_options_into_payload(self):
        builder = RecipeDocumentBuilder()
        options = {'include_scores': True}
        source = DocumentSourceRef(source_type='remedial_variant')
        recipe = DocumentRecipe(
            document_type='remedial_sheet',
            sections=[
                DocumentSectionSpec(
                    section_type='original_mistakes',
                    options=options,
                ),
            ],
        )

        document = builder.build(source, recipe)
        options['include_scores'] = False

        self.assertEqual(
            document.sections[0].payload,
            {'include_scores': True},
        )
