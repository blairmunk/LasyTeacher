from unittest import TestCase

from core_logic.entities.document import (
    DocumentSectionSpec,
    DocumentSourceRef,
    PrintSettingsSpec,
)
from core_logic.entities.document_rendering import (
    DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER,
    DocumentRenderResult,
    GeneratedDocument,
    GeneratedDocumentFile,
)
from core_logic.use_cases.render_document_from_print_settings import (
    RenderDocumentFromPrintSettingsRequest,
    RenderDocumentFromPrintSettingsUseCase,
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


class RenderDocumentFromPrintSettingsUseCaseTests(TestCase):
    def test_delegates_to_recipe_render_use_case(self):
        recipe_use_case = FakeRenderDocumentFromRecipeUseCase()
        use_case = RenderDocumentFromPrintSettingsUseCase(
            render_document_from_recipe_use_case=recipe_use_case,
        )
        print_settings = PrintSettingsSpec(
            name='Work profile',
            document_type=WORK_DOCUMENT_TYPE,
            sections=[DocumentSectionSpec(section_type=HEADER_SECTION)],
        )

        result = use_case.execute(
            RenderDocumentFromPrintSettingsRequest(
                source=DocumentSourceRef(
                    source_type='work',
                    source_id='work-1',
                    title='Контрольная',
                ),
                print_settings_spec=print_settings,
                render_target=RenderTarget(renderer_type='html'),
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(
            recipe_use_case.request.recipe.section_types,
            (HEADER_SECTION,),
        )
        self.assertEqual(recipe_use_case.request.source_name, 'Контрольная')

    def test_renders_document_from_print_settings(self):
        engine = FakeDocumentEngine()
        use_case = RenderDocumentFromPrintSettingsUseCase(
            document_engine=engine,
        )
        print_settings = PrintSettingsSpec(
            name='Work profile',
            document_type=WORK_DOCUMENT_TYPE,
            sections=[
                DocumentSectionSpec(section_type=HEADER_SECTION),
                DocumentSectionSpec(section_type=TASK_LIST_SECTION),
            ],
        )

        result = use_case.execute(
            RenderDocumentFromPrintSettingsRequest(
                source=DocumentSourceRef(
                    source_type='work',
                    source_id='work-1',
                    title='Контрольная',
                ),
                render_target=RenderTarget(renderer_type='html'),
                print_settings_spec=print_settings,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.file_type, 'html')
        self.assertEqual(result.source_name, 'Контрольная')
        self.assertEqual(engine.render_request.source.source_id, 'work-1')
        self.assertEqual(
            engine.render_request.recipe.section_types,
            (HEADER_SECTION, TASK_LIST_SECTION),
        )

    def test_explicit_source_name_overrides_source_title(self):
        engine = FakeDocumentEngine()
        use_case = RenderDocumentFromPrintSettingsUseCase(
            document_engine=engine,
        )

        result = use_case.execute(
            RenderDocumentFromPrintSettingsRequest(
                source=DocumentSourceRef(
                    source_type='work',
                    source_id='work-1',
                    title='Source title',
                ),
                print_settings_spec=PrintSettingsSpec(
                    name='Work profile',
                    document_type=WORK_DOCUMENT_TYPE,
                ),
                render_target=RenderTarget(renderer_type='html'),
                source_name='Display title',
            )
        )

        self.assertEqual(result.source_name, 'Display title')

    def test_rejects_unsupported_renderer_without_engine_call(self):
        engine = FakeDocumentEngine()
        use_case = RenderDocumentFromPrintSettingsUseCase(
            document_engine=engine,
        )

        result = use_case.execute(
            RenderDocumentFromPrintSettingsRequest(
                source=DocumentSourceRef(
                    source_type='work',
                    source_id='work-1',
                ),
                print_settings_spec=PrintSettingsSpec(
                    name='Work profile',
                    document_type=WORK_DOCUMENT_TYPE,
                ),
                render_target=RenderTarget(renderer_type='docx'),
                source_name='Контрольная',
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, DOCUMENT_RENDER_STATUS_UNSUPPORTED_RENDERER)
        self.assertEqual(result.renderer_type, 'docx')
        self.assertIsNone(engine.render_request)


class FakeRenderDocumentFromRecipeUseCase:
    def __init__(self):
        self.request = None

    def execute(self, request):
        self.request = request
        return DocumentRenderResult(
            status='generated',
            renderer_type=request.render_target.renderer_type,
        )
