from unittest import TestCase

from core_logic.entities.document import DocumentRecipe, DocumentSourceRef
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_render_plan import DocumentRenderPlan


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
