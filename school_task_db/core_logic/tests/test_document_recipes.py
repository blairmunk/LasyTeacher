from unittest import TestCase

from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    HEADER_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    WORKSHEET_DOCUMENT_TYPE,
    build_document_recipe_from_sections_config,
)


class DocumentRecipeTests(TestCase):
    def test_builds_recipe_from_template_sections_config(self):
        recipe = build_document_recipe_from_sections_config(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            sections_config=[
                {
                    'type': HEADER_SECTION,
                    'params': {'show_date': True},
                },
                {
                    'type': TASK_LIST_SECTION,
                    'title': 'Блок тренировки',
                    'params': {
                        'section_title': 'Тренировка',
                        'source': 'new_tasks',
                    },
                },
            ],
        )

        self.assertEqual(recipe.document_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(recipe.sections[0].options, {'show_date': True})
        self.assertEqual(recipe.sections[1].title, 'Блок тренировки')
        self.assertEqual(
            recipe.sections[1].options,
            {
                'section_title': 'Тренировка',
                'source': 'new_tasks',
            },
        )

    def test_builds_recipe_from_wrapped_sections_config(self):
        recipe = build_document_recipe_from_sections_config(
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            sections_config={
                'document_type': 'remedial',
                'sections': [
                    {'type': HEADER_SECTION},
                    {
                        'section_type': ANSWERS_SECTION,
                        'options': {'compact': True},
                    },
                ],
            },
        )

        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, ANSWERS_SECTION),
        )
        self.assertEqual(recipe.sections[1].options, {'compact': True})

    def test_rejects_non_mapping_section_params(self):
        with self.assertRaises(ValueError):
            build_document_recipe_from_sections_config(
                document_type=WORKSHEET_DOCUMENT_TYPE,
                sections_config=[
                    {
                        'type': HEADER_SECTION,
                        'params': ['not', 'a', 'mapping'],
                    },
                ],
            )
