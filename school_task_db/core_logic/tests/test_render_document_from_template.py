from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    DocumentSourceRef,
    DocumentTemplateSpec,
)
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    GeneratedDocument,
    GeneratedDocumentFile,
)
from core_logic.use_cases.render_document_from_template import (
    RenderDocumentFromTemplateRequest,
    RenderDocumentFromTemplateUseCase,
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


class RenderDocumentFromTemplateUseCaseTests(TestCase):
    def test_renders_document_from_template_spec(self):
        engine = FakeDocumentEngine()
        use_case = RenderDocumentFromTemplateUseCase(document_engine=engine)
        template_spec = DocumentTemplateSpec(
            name='Work template',
            template_type=WORK_DOCUMENT_TYPE,
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
            ],
        )

        result = use_case.execute(
            RenderDocumentFromTemplateRequest(
                source=DocumentSourceRef(
                    source_type='work',
                    source_id='work-1',
                    title='Контрольная',
                ),
                template_spec=template_spec,
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(result.source_name, 'Контрольная')
        render_plan = engine.render_request
        self.assertEqual(render_plan.source.source_id, 'work-1')
        self.assertEqual(render_plan.recipe.document_type, WORK_DOCUMENT_TYPE)
        self.assertEqual(
            render_plan.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )
        self.assertEqual(render_plan.render_target.renderer_type, 'html')

    def test_explicit_source_name_overrides_source_title(self):
        engine = FakeDocumentEngine()
        use_case = RenderDocumentFromTemplateUseCase(document_engine=engine)

        result = use_case.execute(
            RenderDocumentFromTemplateRequest(
                source=DocumentSourceRef(
                    source_type='work',
                    source_id='work-1',
                    title='Source title',
                ),
                template_spec=DocumentTemplateSpec(
                    name='Work template',
                    template_type=WORK_DOCUMENT_TYPE,
                    sections=[],
                ),
                render_target=RenderTarget(renderer_type='html'),
                source_name='Display title',
            )
        )

        self.assertEqual(result.source_name, 'Display title')

    def test_rejects_unsupported_renderer_without_engine_call(self):
        engine = FakeDocumentEngine()
        use_case = RenderDocumentFromTemplateUseCase(document_engine=engine)

        result = use_case.execute(
            RenderDocumentFromTemplateRequest(
                source=DocumentSourceRef(source_type='work', source_id='work-1'),
                template_spec=DocumentTemplateSpec(
                    name='Work template',
                    template_type=WORK_DOCUMENT_TYPE,
                    sections=[],
                ),
                render_target=RenderTarget(renderer_type='docx'),
                source_name='Контрольная',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER)
        self.assertEqual(result.renderer_type, 'docx')
        self.assertIsNone(engine.render_request)
