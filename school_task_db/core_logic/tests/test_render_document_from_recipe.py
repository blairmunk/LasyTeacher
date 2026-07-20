from unittest import TestCase

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
)
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    GeneratedDocument,
    GeneratedDocumentFile,
)
from core_logic.use_cases.render_document_from_recipe import (
    RenderDocumentFromRecipeRequest,
    RenderDocumentFromRecipeUseCase,
)
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_recipes import (
    HEADER_SECTION,
    TASK_LIST_SECTION,
    WORK_DOCUMENT_TYPE,
)


class FakeDocumentEngine:
    def __init__(self):
        self.render_request = None
        self.document = GeneratedDocument(
            file_type='html',
            files=[GeneratedDocumentFile(filename='work.html', size_kb=1.0)],
        )

    def render_document(self, render_plan):
        self.render_request = render_plan
        return self.document


class RenderDocumentFromRecipeUseCaseTests(TestCase):
    def test_renders_document_from_recipe(self):
        engine = FakeDocumentEngine()
        use_case = RenderDocumentFromRecipeUseCase(document_engine=engine)
        recipe = DocumentRecipe(
            document_type=WORK_DOCUMENT_TYPE,
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
            ],
        )

        result = use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=DocumentSourceRef(
                    source_type='work',
                    source_id='work-1',
                    title='Контрольная',
                ),
                recipe=recipe,
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertEqual(engine.render_request.recipe, recipe)
        self.assertEqual(engine.render_request.source.source_id, 'work-1')
        self.assertEqual(engine.render_request.render_target.renderer_type, 'html')

    def test_uses_empty_status_for_empty_document(self):
        engine = FakeDocumentEngine()
        engine.document = GeneratedDocument(file_type='html')
        use_case = RenderDocumentFromRecipeUseCase(document_engine=engine)

        result = use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=DocumentSourceRef(source_type='work', source_id='work-1'),
                recipe=DocumentRecipe(document_type=WORK_DOCUMENT_TYPE),
                render_target=RenderTarget(renderer_type='html'),
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_EMPTY)

    def test_rejects_unsupported_renderer_without_engine_call(self):
        engine = FakeDocumentEngine()
        use_case = RenderDocumentFromRecipeUseCase(document_engine=engine)

        result = use_case.execute(
            RenderDocumentFromRecipeRequest(
                source=DocumentSourceRef(source_type='work', source_id='work-1'),
                recipe=DocumentRecipe(document_type=WORK_DOCUMENT_TYPE),
                render_target=RenderTarget(renderer_type='docx'),
                source_name='Контрольная',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER)
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertIsNone(engine.render_request)
