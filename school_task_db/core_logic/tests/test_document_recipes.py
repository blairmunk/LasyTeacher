from unittest import TestCase

from core_logic.value_objects.document_render_options import (
    RemedialSheetBuildOptions,
    WorkDocumentBuildOptions,
)
from core_logic.value_objects.document_recipe_factories import (
    build_remedial_sheet_document_recipe,
    build_work_document_recipe,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
    ORIGINAL_MISTAKES_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TRAINING_TASKS_SECTION,
    build_document_recipe_from_sections_config,
    build_document_template_spec_from_config,
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
                document_type=WORKSHEET_DOCUMENT_TYPE,
                sections_config=[
                    {
                        'type': HEADER_SECTION,
                        'params': ['not', 'a', 'mapping'],
                    },
                ],
            )

    def test_builds_template_spec_from_sections_config(self):
        template = build_document_template_spec_from_config(
            name='Рабочий лист',
            template_type=WORKSHEET_DOCUMENT_TYPE,
            sections_config={
                'sections': [
                    {'type': HEADER_SECTION},
                    {
                        'type': TASK_LIST_SECTION,
                        'params': {'source': 'new_tasks'},
                    },
                ],
            },
            default_content_config={'answer_type': 'tasks_only'},
        )

        self.assertEqual(template.name, 'Рабочий лист')
        self.assertEqual(template.template_type, WORKSHEET_DOCUMENT_TYPE)
        self.assertEqual(
            template.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(
            template.default_content_config,
            {'answer_type': 'tasks_only'},
        )
        self.assertEqual(
            template.to_recipe().document_type,
            WORKSHEET_DOCUMENT_TYPE,
        )

    def test_default_work_recipe_contains_header_and_task_list(self):
        recipe = build_work_document_recipe()

        self.assertEqual(recipe.document_type, WORK_DOCUMENT_TYPE)
        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
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
