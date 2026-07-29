from unittest import TestCase

from core_logic.entities.document import (
    DocumentPresentation,
    PrintSettingsSpec,
    REMEDIAL_WORK_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan_factories import (
    build_remedial_sheet_document_recipe_for_render,
    build_remedial_sheet_batch_document_render_plan,
    build_remedial_sheet_document_render_plan,
    build_remedial_sheet_document_source,
    build_work_document_recipe_for_render,
    build_work_document_render_plan,
    build_work_document_source,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    HEADER_SECTION,
    PAGE_BREAK_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    WORK_DOCUMENT_TYPE,
)


class DocumentRenderPlanFactoriesTests(TestCase):
    def test_build_work_document_source(self):
        source = build_work_document_source(
            work_id='work-1',
            work_name='Контрольная',
        )

        self.assertEqual(source.source_type, WORK_SOURCE_TYPE)
        self.assertEqual(source.source_id, 'work-1')
        self.assertEqual(source.title, 'Контрольная')

    def test_build_remedial_sheet_document_source(self):
        source = build_remedial_sheet_document_source('variant-1')

        self.assertEqual(source.source_type, REMEDIAL_VARIANT_SOURCE_TYPE)
        self.assertEqual(source.source_id, 'variant-1')
        self.assertEqual(source.title, 'Работа над ошибками')

    def test_build_work_document_recipe_for_render(self):
        recipe = build_work_document_recipe_for_render(
            WorkDocumentRenderOptions(
                renderer_type='html',
                append_answers=True,
            ),
        )

        self.assertEqual(recipe.document_type, WORK_DOCUMENT_TYPE)
        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION, ANSWERS_SECTION),
        )

    def test_build_work_document_recipe_keeps_default_sections_with_profile(self):
        presentation = DocumentPresentation(custom_css='body {}')
        print_settings = PrintSettingsSpec(
            name='Кастомная работа',
            document_type=WORK_DOCUMENT_TYPE,
            presentation=presentation,
        )

        recipe = build_work_document_recipe_for_render(
            WorkDocumentRenderOptions(renderer_type='html'),
            print_settings_spec=print_settings,
        )

        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(recipe.presentation, presentation)

    def test_build_remedial_sheet_document_recipe_for_render(self):
        recipe = build_remedial_sheet_document_recipe_for_render(
            RemedialSheetDocumentRenderOptions(
                renderer_type='pdf',
                answer_type='with_answers',
            ),
        )

        self.assertEqual(recipe.document_type, REMEDIAL_SHEET_DOCUMENT_TYPE)
        self.assertIn(ANSWERS_SECTION, recipe.section_types)

    def test_build_work_document_render_plan(self):
        plan = build_work_document_render_plan(
            work_id='work-1',
            work_name='Контрольная',
            options=WorkDocumentRenderOptions(
                renderer_type='html',
                append_answers=True,
            ),
        )

        self.assertEqual(plan.source.source_type, WORK_SOURCE_TYPE)
        self.assertEqual(plan.source.source_id, 'work-1')
        self.assertEqual(plan.source.title, 'Контрольная')
        self.assertEqual(plan.render_target.renderer_type, 'html')
        self.assertEqual(
            plan.recipe.section_types,
            ('header', 'task_list', 'answers'),
        )

    def test_build_work_document_render_plan_uses_profile_presentation(self):
        presentation = DocumentPresentation(custom_css='.task {}')
        print_settings = PrintSettingsSpec(
            name='Рабочий лист',
            document_type='work',
            presentation=presentation,
        )

        plan = build_work_document_render_plan(
            work_id='work-1',
            work_name='Контрольная',
            options=WorkDocumentRenderOptions(renderer_type='html'),
            print_settings_spec=print_settings,
        )

        self.assertEqual(plan.recipe.document_type, 'work')
        self.assertEqual(
            plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(plan.recipe.presentation, presentation)

    def test_build_work_document_render_plan_repeats_sections_per_variant(self):
        plan = build_work_document_render_plan(
            work_id='work-1',
            work_name='Контрольная',
            options=WorkDocumentRenderOptions(renderer_type='html'),
            variant_ids=['variant-1', 'variant-2'],
        )

        self.assertEqual(
            plan.recipe.section_types,
            (
                HEADER_SECTION,
                TASK_LIST_SECTION,
                PAGE_BREAK_SECTION,
                HEADER_SECTION,
                TASK_LIST_SECTION,
            ),
        )
        self.assertEqual(
            [
                section.options.get('variant_id')
                for section in plan.recipe.sections
            ],
            ['variant-1', 'variant-1', None, 'variant-2', 'variant-2'],
        )
        self.assertFalse(
            plan.recipe.sections[1].options['show_variant_heading'],
        )
        self.assertFalse(
            plan.recipe.sections[4].options['show_variant_heading'],
        )

    def test_work_print_overrides_apply_on_top_of_default_recipe(self):
        print_settings_spec = PrintSettingsSpec(
            name='Профиль',
            document_type=WORK_DOCUMENT_TYPE,
        )

        recipe = build_work_document_recipe_for_render(
            WorkDocumentRenderOptions(
                renderer_type='html',
                hide_theory=True,
                hide_blank_cells=True,
                append_answers=True,
            ),
            print_settings_spec=print_settings_spec,
        )

        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION, ANSWERS_SECTION),
        )
        self.assertEqual(
            recipe.sections[1].options['hidden_content_types'],
            ['theory'],
        )
        self.assertTrue(recipe.sections[1].options['hide_blank_cells'])


    def test_build_work_document_render_plan_can_disable_variant_breaks(self):
        plan = build_work_document_render_plan(
            work_id='work-1',
            work_name='Контрольная',
            options=WorkDocumentRenderOptions(
                renderer_type='html',
                break_between_variants=False,
            ),
            variant_ids=['variant-1', 'variant-2'],
        )

        self.assertEqual(
            plan.recipe.section_types,
            (
                HEADER_SECTION,
                TASK_LIST_SECTION,
                HEADER_SECTION,
                TASK_LIST_SECTION,
            ),
        )

    def test_build_remedial_sheet_document_render_plan(self):
        plan = build_remedial_sheet_document_render_plan(
            variant_id='variant-1',
            options=RemedialSheetDocumentRenderOptions(
                renderer_type='pdf',
                answer_type='with_full_solutions',
            ),
        )

        self.assertEqual(
            plan.source.source_type,
            REMEDIAL_VARIANT_SOURCE_TYPE,
        )
        self.assertEqual(plan.source.source_id, 'variant-1')
        self.assertEqual(plan.render_target.renderer_type, 'pdf')
        self.assertEqual(
            plan.recipe.section_types,
            (
                'header',
                'original_mistakes',
                'page_break',
                'training_tasks',
                'page_break',
                'answers',
                'page_break',
                'short_solutions',
                'page_break',
                'full_solutions',
            ),
        )

    def test_remedial_profile_does_not_replace_content_recipe(self):
        presentation = DocumentPresentation(custom_latex_preamble='\\small')
        print_settings = PrintSettingsSpec(
            name='Кастомная работа над ошибками',
            document_type='remedial_sheet',
            presentation=presentation,
        )

        plan = build_remedial_sheet_document_render_plan(
            variant_id='variant-1',
            options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            print_settings_spec=print_settings,
        )

        self.assertEqual(plan.recipe.document_type, 'remedial_sheet')
        self.assertEqual(
            plan.recipe.section_types,
            (
                'header',
                'original_mistakes',
                'page_break',
                'training_tasks',
                'page_break',
                'answers',
                'page_break',
                'short_solutions',
            ),
        )
        self.assertEqual(plan.recipe.presentation, presentation)

    def test_build_remedial_sheet_batch_document_render_plan_repeats_sections(self):
        plan = build_remedial_sheet_batch_document_render_plan(
            work_id='work-1',
            work_name='Работа над ошибками',
            variant_ids=['variant-1', 'variant-2'],
            options=RemedialSheetDocumentRenderOptions(
                renderer_type='html',
                answer_type='with_answers',
            ),
        )

        self.assertEqual(plan.source.source_type, REMEDIAL_WORK_SOURCE_TYPE)
        self.assertEqual(plan.source.source_id, 'work-1')
        self.assertEqual(plan.source.title, 'Работа над ошибками')
        self.assertEqual(
            plan.recipe.section_types,
            (
                'header',
                'original_mistakes',
                'page_break',
                'training_tasks',
                'page_break',
                'answers',
                'page_break',
                'header',
                'original_mistakes',
                'page_break',
                'training_tasks',
                'page_break',
                'answers',
            ),
        )
        self.assertEqual(plan.recipe.sections[0].options['variant_id'], 'variant-1')
        self.assertEqual(plan.recipe.sections[7].options['variant_id'], 'variant-2')

    def test_build_remedial_sheet_batch_document_render_plan_uses_print_settings_spec(self):
        presentation = DocumentPresentation(
            custom_css='.remedial-sheet { font-size: 12pt; }',
            custom_latex_preamble='\\usepackage{multicol}',
        )
        print_settings_spec = PrintSettingsSpec(
            name='Профиль РнО',
            document_type='remedial_sheet',
            presentation=presentation,
        )

        plan = build_remedial_sheet_batch_document_render_plan(
            work_id='work-1',
            work_name='Работа над ошибками',
            variant_ids=['variant-1'],
            options=RemedialSheetDocumentRenderOptions(renderer_type='html'),
            print_settings_spec=print_settings_spec,
        )

        self.assertEqual(
            plan.recipe.section_types,
            (
                'header',
                'original_mistakes',
                'page_break',
                'training_tasks',
                'page_break',
                'answers',
                'page_break',
                'short_solutions',
            ),
        )
        self.assertEqual(plan.recipe.sections[0].options['variant_id'], 'variant-1')
        self.assertEqual(plan.recipe.presentation, presentation)
