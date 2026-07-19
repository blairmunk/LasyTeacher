from unittest import TestCase

from core_logic.value_objects.content_config import (
    RemedialSheetBuildOptions,
    WorkDocumentBuildOptions,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    TASK_LIST_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_VARIANTS_SECTION,
    TRAINING_TASKS_SECTION,
    build_document_recipe_from_sections_config,
    build_remedial_sheet_document_recipe,
    build_work_document_recipe,
)


class DocumentRecipeTests(TestCase):
    def test_builds_recipe_from_template_sections_config(self):
        recipe = build_document_recipe_from_sections_config(
            document_type='worksheet',
            sections_config=[
                {
                    'type': HEADER_SECTION,
                    'params': {'show_date': True},
                },
                {
                    'type': TASK_LIST_SECTION,
                    'params': {
                        'section_title': 'Тренировка',
                        'source': 'new_tasks',
                    },
                },
            ],
        )

        self.assertEqual(recipe.document_type, 'worksheet')
        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(recipe.sections[0].options, {'show_date': True})
        self.assertEqual(
            recipe.sections[1].options,
            {
                'section_title': 'Тренировка',
                'source': 'new_tasks',
            },
        )

    def test_builds_recipe_from_wrapped_sections_config(self):
        recipe = build_document_recipe_from_sections_config(
            document_type='remedial_sheet',
            sections_config={
                'template_type': 'remedial',
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
                document_type='worksheet',
                sections_config=[
                    {
                        'type': HEADER_SECTION,
                        'params': ['not', 'a', 'mapping'],
                    },
                ],
            )

    def test_default_work_recipe_contains_header_and_task_variants(self):
        recipe = build_work_document_recipe()

        self.assertEqual(recipe.document_type, 'work')
        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_VARIANTS_SECTION),
        )
        self.assertEqual(
            recipe.sections[1].options,
            {
                'include_hints': False,
                'include_instructions': False,
            },
        )

    def test_work_recipe_maps_answer_options_to_sections(self):
        recipe = build_work_document_recipe(
            WorkDocumentBuildOptions(
                answer_type='with_full_solutions',
                include_hints=True,
                include_instructions=True,
            )
        )

        self.assertEqual(
            recipe.section_types,
            (
                HEADER_SECTION,
                TASK_VARIANTS_SECTION,
                ANSWERS_SECTION,
                SHORT_SOLUTIONS_SECTION,
                FULL_SOLUTIONS_SECTION,
            ),
        )
        self.assertEqual(
            recipe.sections[1].options,
            {
                'include_hints': True,
                'include_instructions': True,
            },
        )

    def test_default_remedial_sheet_recipe_contains_review_and_training(self):
        recipe = build_remedial_sheet_document_recipe()

        self.assertEqual(recipe.document_type, 'remedial_sheet')
        self.assertEqual(
            recipe.section_types,
            (
                HEADER_SECTION,
                ORIGINAL_MISTAKES_SECTION,
                TRAINING_TASKS_SECTION,
                ANSWERS_SECTION,
                SHORT_SOLUTIONS_SECTION,
            ),
        )
        self.assertEqual(
            recipe.sections[1].options,
            {'include_scores': True},
        )
        self.assertEqual(
            recipe.sections[2].options,
            {'include_scores': False},
        )

    def test_remedial_sheet_recipe_maps_full_solutions(self):
        recipe = build_remedial_sheet_document_recipe(
            RemedialSheetBuildOptions(answer_type='with_full_solutions')
        )

        self.assertEqual(
            recipe.section_types,
            (
                HEADER_SECTION,
                ORIGINAL_MISTAKES_SECTION,
                TRAINING_TASKS_SECTION,
                ANSWERS_SECTION,
                SHORT_SOLUTIONS_SECTION,
                FULL_SOLUTIONS_SECTION,
            ),
        )
