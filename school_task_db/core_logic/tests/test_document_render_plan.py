from unittest import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSourceRef,
)
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    RenderTarget,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderPlan,
    DocumentRenderRequest,
    build_remedial_sheet_document_render_plan,
    build_work_document_render_plan,
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

    def test_render_request_groups_document_and_target(self):
        document = Document(title='Контрольная')
        render_target = RenderTarget(renderer_type='pdf')

        request = DocumentRenderRequest(
            document=document,
            render_target=render_target,
        )

        self.assertEqual(request.document.title, 'Контрольная')
        self.assertEqual(request.render_target.renderer_type, 'pdf')

    def test_build_work_document_render_plan(self):
        plan = build_work_document_render_plan(
            work_id='work-1',
            work_name='Контрольная',
            options=WorkDocumentRenderOptions(
                renderer_type='html',
                answer_type='with_answers',
            ),
        )

        self.assertEqual(plan.source.source_type, 'work')
        self.assertEqual(plan.source.source_id, 'work-1')
        self.assertEqual(plan.source.title, 'Контрольная')
        self.assertEqual(plan.render_target.renderer_type, 'html')
        self.assertEqual(
            plan.recipe.section_types,
            ('header', 'task_variants', 'answers'),
        )

    def test_build_remedial_sheet_document_render_plan(self):
        plan = build_remedial_sheet_document_render_plan(
            variant_id='variant-1',
            options=RemedialSheetDocumentRenderOptions(
                renderer_type='pdf',
                answer_type='with_full_solutions',
            ),
        )

        self.assertEqual(plan.source.source_type, 'remedial_variant')
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
