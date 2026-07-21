from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    DocumentTemplateSpec,
    REMEDIAL_WORK_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
    WORK_DOCUMENT_STYLE_WORKSHEET,
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
    COMMON_HEADER_SECTION,
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
                answer_type='with_answers',
            ),
        )

        self.assertEqual(recipe.document_type, WORK_DOCUMENT_TYPE)
        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION, ANSWERS_SECTION),
        )

    def test_build_work_document_recipe_for_render_supports_worksheet_style(self):
        recipe = build_work_document_recipe_for_render(
            WorkDocumentRenderOptions(
                renderer_type='html',
                document_style=WORK_DOCUMENT_STYLE_WORKSHEET,
            ),
        )

        self.assertEqual(recipe.document_type, WORK_DOCUMENT_TYPE)
        self.assertEqual(
            recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertIn('role_render_modes', recipe.sections[1].options)
        self.assertIn('role_blank_cells', recipe.sections[1].options)

    def test_build_work_document_recipe_for_render_uses_template_spec(self):
        template_spec = DocumentTemplateSpec(
            name='Кастомная работа',
            template_type=WORK_DOCUMENT_TYPE,
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )

        recipe = build_work_document_recipe_for_render(
            WorkDocumentRenderOptions(renderer_type='html'),
            template_spec=template_spec,
        )

        self.assertEqual(recipe.section_types, (HEADER_SECTION,))

    def test_template_spec_takes_priority_over_worksheet_style(self):
        template_spec = DocumentTemplateSpec(
            name='Кастомная работа',
            template_type=WORK_DOCUMENT_TYPE,
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )

        recipe = build_work_document_recipe_for_render(
            WorkDocumentRenderOptions(
                renderer_type='html',
                document_style=WORK_DOCUMENT_STYLE_WORKSHEET,
            ),
            template_spec=template_spec,
        )

        self.assertEqual(recipe.section_types, (HEADER_SECTION,))

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
                answer_type='with_answers',
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

    def test_build_work_document_render_plan_uses_template_spec(self):
        template_spec = DocumentTemplateSpec(
            name='Рабочий лист',
            template_type='work',
            sections=[
                DocumentSectionSpec(
                    section_type=TASK_LIST_SECTION,
                    options={'source': 'new_tasks'},
                ),
                DocumentSectionSpec(section_type=ANSWERS_SECTION),
            ],
        )

        plan = build_work_document_render_plan(
            work_id='work-1',
            work_name='Контрольная',
            options=WorkDocumentRenderOptions(renderer_type='html'),
            template_spec=template_spec,
        )

        self.assertEqual(plan.recipe.document_type, 'work')
        self.assertEqual(
            plan.recipe.section_types,
            (TASK_LIST_SECTION, ANSWERS_SECTION),
        )
        self.assertEqual(
            plan.recipe.sections[0].options,
            {'source': 'new_tasks'},
        )

    def test_build_work_document_render_plan_repeats_sections_per_variant(self):
        template_spec = DocumentTemplateSpec(
            name='Работа по вариантам',
            template_type='work',
            sections=[
                DocumentSectionSpec(section_type=COMMON_HEADER_SECTION),
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
            ],
        )

        plan = build_work_document_render_plan(
            work_id='work-1',
            work_name='Контрольная',
            options=WorkDocumentRenderOptions(renderer_type='html'),
            template_spec=template_spec,
            variant_ids=['variant-1', 'variant-2'],
        )

        self.assertEqual(
            plan.recipe.section_types,
            (
                COMMON_HEADER_SECTION,
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
            [None, 'variant-1', 'variant-1', None, 'variant-2', 'variant-2'],
        )

    def test_build_work_document_render_plan_can_disable_variant_breaks(self):
        template_spec = DocumentTemplateSpec(
            name='Сплошная работа',
            template_type='work',
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
            ],
        )

        plan = build_work_document_render_plan(
            work_id='work-1',
            work_name='Контрольная',
            options=WorkDocumentRenderOptions(
                renderer_type='html',
                break_between_variants=False,
            ),
            template_spec=template_spec,
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
                'training_tasks',
                'answers',
                'short_solutions',
                'full_solutions',
            ),
        )

    def test_build_remedial_sheet_document_render_plan_uses_template_spec(self):
        template_spec = DocumentTemplateSpec(
            name='Кастомная работа над ошибками',
            template_type='remedial_sheet',
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
            ],
        )

        plan = build_remedial_sheet_document_render_plan(
            variant_id='variant-1',
            options=RemedialSheetDocumentRenderOptions(renderer_type='pdf'),
            template_spec=template_spec,
        )

        self.assertEqual(plan.recipe.document_type, 'remedial_sheet')
        self.assertEqual(
            plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )

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
                'training_tasks',
                'answers',
                'page_break',
                'header',
                'original_mistakes',
                'training_tasks',
                'answers',
            ),
        )
        self.assertEqual(plan.recipe.sections[0].options['variant_id'], 'variant-1')
        self.assertEqual(plan.recipe.sections[5].options['variant_id'], 'variant-2')
