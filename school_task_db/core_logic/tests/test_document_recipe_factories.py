from unittest import TestCase

from core_logic.value_objects.document_recipe_factories import (
    build_remedial_sheet_document_recipe,
    build_work_document_recipe,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    PAGE_BREAK_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetBuildOptions,
    WorkDocumentBuildOptions,
)


class DocumentRecipeFactoriesTests(TestCase):
    def test_default_work_recipe_contains_header_and_task_list(self):
        recipe = build_work_document_recipe()

        self.assertEqual(recipe.document_type, WORK_DOCUMENT_TYPE)
        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION, PAGE_BREAK_SECTION),
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
                TASK_LIST_SECTION,
                ANSWERS_SECTION,
                SHORT_SOLUTIONS_SECTION,
                FULL_SOLUTIONS_SECTION,
                PAGE_BREAK_SECTION,
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

        self.assertEqual(recipe.document_type, REMEDIAL_SHEET_DOCUMENT_TYPE)
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
