from unittest import TestCase

from core_logic.entities.document import DocumentRecipe, DocumentSourceRef
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_EMPTY,
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    GeneratedDocument,
    GeneratedDocumentFile,
)
from core_logic.use_cases.render_document import (
    RenderDocumentRequest,
    RenderDocumentUseCase,
)
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_plan import (
    build_document_render_plan,
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


class RenderDocumentUseCaseTests(TestCase):
    def test_render_document_delegates_to_engine(self):
        service = FakeDocumentEngine()
        use_case = RenderDocumentUseCase(document_engine=service)
        render_plan = build_document_render_plan(
            source=DocumentSourceRef(
                source_type='work',
                source_id='work-1',
                title='Контрольная',
            ),
            recipe=DocumentRecipe(document_type='work'),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = use_case.execute(
            RenderDocumentRequest(
                render_plan=render_plan,
                source_name='Контрольная',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertEqual(service.render_request, render_plan)

    def test_render_document_rejects_unsupported_renderer(self):
        service = FakeDocumentEngine()
        use_case = RenderDocumentUseCase(document_engine=service)
        render_plan = build_document_render_plan(
            source=DocumentSourceRef(source_type='work', source_id='work-1'),
            recipe=DocumentRecipe(document_type='work'),
            render_target=RenderTarget(renderer_type='docx'),
        )

        result = use_case.execute(
            RenderDocumentRequest(
                render_plan=render_plan,
                source_name='Контрольная',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER)
        self.assertEqual(result.renderer_type, 'docx')
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertIsNone(service.render_request)

    def test_render_document_uses_empty_status_for_empty_files(self):
        service = FakeDocumentEngine()
        service.document = GeneratedDocument(file_type='html')
        use_case = RenderDocumentUseCase(document_engine=service)
        render_plan = build_document_render_plan(
            source=DocumentSourceRef(source_type='work', source_id='work-1'),
            recipe=DocumentRecipe(document_type='work'),
            render_target=RenderTarget(renderer_type='html'),
        )

        result = use_case.execute(
            RenderDocumentRequest(
                render_plan=render_plan,
                empty_status=DOCUMENT_RENDER_STATUS_EMPTY,
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_EMPTY)
