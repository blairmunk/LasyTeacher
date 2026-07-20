from unittest import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSection,
    DocumentSourceRef,
    DocumentSectionSpec,
    DocumentTemplateSpec,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
    RenderTarget,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderPlan,
    DocumentRenderRequest,
    DocumentSectionRenderRequest,
    build_document_render_plan,
)
from core_logic.value_objects.document_render_plan_factories import (
    build_remedial_sheet_document_render_plan,
    build_work_document_render_plan,
)
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    HEADER_SECTION,
    TASK_LIST_SECTION,
)


class DocumentRenderPlanTests(TestCase):
    def test_render_plan_groups_source_recipe_and_target(self):
        source = DocumentSourceRef(
            source_type='work',
            source_id='work-1',
            title='Контрольная',
        )
        recipe = DocumentRecipe(document_type='work')
        render_target = RenderTarget(renderer_type='html', page_format='A5')

        plan = DocumentRenderPlan(
            source=source,
            recipe=recipe,
            render_target=render_target,
        )

        self.assertEqual(plan.source.source_id, 'work-1')
        self.assertEqual(plan.recipe.document_type, 'work')
        self.assertEqual(plan.render_target.renderer_type, 'html')

    def test_build_document_render_plan_from_generic_parts(self):
        source = DocumentSourceRef(
            source_type='custom',
            source_id='source-1',
            title='Документ',
        )
        recipe = DocumentRecipe(document_type='custom')
        render_target = RenderTarget(renderer_type='html')

        plan = build_document_render_plan(
            source=source,
            recipe=recipe,
            render_target=render_target,
        )

        self.assertEqual(plan.source, source)
        self.assertEqual(plan.recipe, recipe)
        self.assertEqual(plan.render_target, render_target)

    def test_render_request_groups_document_and_target(self):
        document = Document(title='Контрольная')
        render_target = RenderTarget(renderer_type='pdf')

        request = DocumentRenderRequest(
            document=document,
            render_target=render_target,
        )

        self.assertEqual(request.document.title, 'Контрольная')
        self.assertEqual(request.render_target.renderer_type, 'pdf')

    def test_section_render_request_groups_document_section_and_target(self):
        document = Document(title='Контрольная')
        section = DocumentSection(section_type='task_list')
        render_target = RenderTarget(renderer_type='html')

        request = DocumentSectionRenderRequest(
            document=document,
            section=section,
            render_target=render_target,
        )

        self.assertEqual(request.document.title, 'Контрольная')
        self.assertEqual(request.section.section_type, 'task_list')
        self.assertEqual(request.render_target.renderer_type, 'html')

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
