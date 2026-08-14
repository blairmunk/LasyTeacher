from unittest import TestCase

from core_logic.entities.document import (
    DocumentPresentation,
    DocumentPresentationProfile,
    REMEDIAL_WORK_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetPrintOptions,
    WorkDocumentPrintOverrides,
)
from core_logic.value_objects.document_render_recipe_factories import (
    build_remedial_sheet_batch_document_recipe_for_render,
    build_remedial_sheet_document_recipe_for_render,
    build_work_document_recipe_for_render,
)
from core_logic.value_objects.document_source_factories import (
    build_remedial_sheet_batch_document_source,
    build_remedial_sheet_document_source,
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


class DocumentRenderRecipeFactoriesTests(TestCase):
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
            WorkDocumentPrintOverrides(
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
        presentation_profile = DocumentPresentationProfile(
            name='Кастомная работа',
            document_type=WORK_DOCUMENT_TYPE,
            presentation=presentation,
        )

        recipe = build_work_document_recipe_for_render(
            WorkDocumentPrintOverrides(),
            presentation_profile=presentation_profile,
        )

        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(recipe.presentation, presentation)

    def test_work_recipe_ignores_profile_for_another_document_type(self):
        presentation_profile = DocumentPresentationProfile(
            name='Профиль РнО',
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            presentation=DocumentPresentation(custom_css='.foreign {}'),
        )

        recipe = build_work_document_recipe_for_render(
            WorkDocumentPrintOverrides(),
            presentation_profile=presentation_profile,
        )

        self.assertFalse(recipe.presentation.has_customization)

    def test_build_remedial_sheet_document_recipe_for_render(self):
        recipe = build_remedial_sheet_document_recipe_for_render(
            RemedialSheetPrintOptions(
                answer_type='with_answers',
            ),
        )

        self.assertEqual(recipe.document_type, REMEDIAL_SHEET_DOCUMENT_TYPE)
        self.assertIn(ANSWERS_SECTION, recipe.section_types)

    def test_build_work_document_recipe_repeats_sections_per_variant(self):
        recipe = build_work_document_recipe_for_render(
            print_overrides=WorkDocumentPrintOverrides(),
            variant_ids=['variant-1', 'variant-2'],
        )

        self.assertEqual(
            recipe.section_types,
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
                for section in recipe.sections
            ],
            ['variant-1', 'variant-1', None, 'variant-2', 'variant-2'],
        )
        self.assertFalse(
            recipe.sections[1].options['show_variant_heading'],
        )
        self.assertFalse(
            recipe.sections[4].options['show_variant_heading'],
        )

    def test_work_print_overrides_apply_on_top_of_default_recipe(self):
        presentation_profile = DocumentPresentationProfile(
            name='Профиль',
            document_type=WORK_DOCUMENT_TYPE,
        )

        recipe = build_work_document_recipe_for_render(
            WorkDocumentPrintOverrides(
                hide_theory=True,
                hide_blank_cells=True,
                append_answers=True,
            ),
            presentation_profile=presentation_profile,
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

    def test_work_print_overrides_can_hide_task_page_breaks(self):
        recipe = build_work_document_recipe_for_render(
            WorkDocumentPrintOverrides(include_task_page_breaks=False),
        )

        self.assertTrue(
            recipe.sections[1].options['hide_task_page_breaks'],
        )

    def test_build_work_document_recipe_can_disable_variant_breaks(self):
        recipe = build_work_document_recipe_for_render(
            print_overrides=WorkDocumentPrintOverrides(
                break_between_variants=False,
            ),
            variant_ids=['variant-1', 'variant-2'],
        )

        self.assertEqual(
            recipe.section_types,
            (
                HEADER_SECTION,
                TASK_LIST_SECTION,
                HEADER_SECTION,
                TASK_LIST_SECTION,
            ),
        )

    def test_build_remedial_sheet_recipe_with_full_solutions(self):
        recipe = build_remedial_sheet_document_recipe_for_render(
            print_options=RemedialSheetPrintOptions(
                answer_type='with_full_solutions',
            ),
        )
        self.assertEqual(
            recipe.section_types,
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
        presentation_profile = DocumentPresentationProfile(
            name='Кастомная работа над ошибками',
            document_type='remedial_sheet',
            presentation=presentation,
        )

        recipe = build_remedial_sheet_document_recipe_for_render(
            print_options=RemedialSheetPrintOptions(),
            presentation_profile=presentation_profile,
        )

        self.assertEqual(recipe.document_type, 'remedial_sheet')
        self.assertEqual(
            recipe.section_types,
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
        self.assertEqual(recipe.presentation, presentation)

    def test_build_remedial_sheet_batch_recipe_repeats_sections(self):
        source = build_remedial_sheet_batch_document_source(
            work_id='work-1',
            work_name='Работа над ошибками',
        )
        recipe = build_remedial_sheet_batch_document_recipe_for_render(
            variant_ids=['variant-1', 'variant-2'],
            print_options=RemedialSheetPrintOptions(
                answer_type='with_answers',
            ),
        )

        self.assertEqual(source.source_type, REMEDIAL_WORK_SOURCE_TYPE)
        self.assertEqual(source.source_id, 'work-1')
        self.assertEqual(source.title, 'Работа над ошибками')
        self.assertEqual(
            recipe.section_types,
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
        self.assertEqual(recipe.sections[0].options['variant_id'], 'variant-1')
        self.assertEqual(recipe.sections[7].options['variant_id'], 'variant-2')

    def test_build_remedial_sheet_batch_recipe_uses_presentation_profile(self):
        presentation = DocumentPresentation(
            custom_css='.remedial-sheet { font-size: 12pt; }',
            custom_latex_preamble='\\usepackage{multicol}',
        )
        presentation_profile = DocumentPresentationProfile(
            name='Профиль РнО',
            document_type='remedial_sheet',
            presentation=presentation,
        )

        recipe = build_remedial_sheet_batch_document_recipe_for_render(
            variant_ids=['variant-1'],
            print_options=RemedialSheetPrintOptions(),
            presentation_profile=presentation_profile,
        )

        self.assertEqual(
            recipe.section_types,
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
        self.assertEqual(recipe.sections[0].options['variant_id'], 'variant-1')
        self.assertEqual(recipe.presentation, presentation)
