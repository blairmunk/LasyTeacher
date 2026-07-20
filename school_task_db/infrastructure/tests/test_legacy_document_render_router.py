from unittest import TestCase

from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.value_objects.content_config import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
)
from infrastructure.services.legacy_document_render_router import (
    LegacyDocumentRenderRouter,
)


class LegacyDocumentRenderRouterTests(TestCase):
    def test_routes_html_work_rendering(self):
        file_renderer = FakeLegacyFileRenderer()
        file_store = FakeRenderedDocumentFileStore()
        router = LegacyDocumentRenderRouter(
            legacy_file_renderer=file_renderer,
            file_store=file_store,
        )

        result = router.render_work(
            work='work-object',
            options=WorkDocumentRenderOptions(renderer_type='html'),
        )

        self.assertEqual(result.file_type, 'html')
        self.assertEqual(
            file_renderer.calls,
            [('render_html_work', 'work-object')],
        )
        self.assertEqual(file_store.path_requests, [('html', ['work.html'])])

    def test_routes_latex_work_rendering_with_page_format(self):
        file_renderer = FakeLegacyFileRenderer()
        file_store = FakeRenderedDocumentFileStore()
        router = LegacyDocumentRenderRouter(
            legacy_file_renderer=file_renderer,
            file_store=file_store,
        )

        result = router.render_work(
            work='work-object',
            options=WorkDocumentRenderOptions(
                renderer_type='latex',
                pdf_format='A5',
            ),
        )

        self.assertEqual(result.file_type, 'latex')
        self.assertEqual(
            file_renderer.calls,
            [('render_latex_work', 'work-object', 'A5')],
        )
        self.assertEqual(file_store.path_requests, [('latex', ['work.tex'])])

    def test_routes_pdf_remedial_rendering_with_page_format(self):
        file_renderer = FakeLegacyFileRenderer()
        file_store = FakeRenderedDocumentFileStore()
        router = LegacyDocumentRenderRouter(
            legacy_file_renderer=file_renderer,
            file_store=file_store,
        )

        result = router.render_remedial_sheet(
            variant='variant-object',
            options=RemedialSheetDocumentRenderOptions(
                renderer_type='pdf',
                pdf_format='A5',
            ),
        )

        self.assertEqual(result.file_type, 'pdf')
        self.assertEqual(
            file_renderer.calls,
            [('render_remedial_pdf', 'variant-object', 'A5')],
        )
        self.assertEqual(file_store.path_requests, [('pdf', ['remedial.pdf'])])


class FakeLegacyFileRenderer:
    def __init__(self):
        self.calls = []

    def render_latex_work(self, work, content_config, page_format='A4'):
        self.calls.append(('render_latex_work', work, page_format))
        return ['work.tex']

    def render_html_work(self, work, content_config):
        self.calls.append(('render_html_work', work))
        return ['work.html']

    def render_pdf_work(self, work, content_config, page_format='A4'):
        self.calls.append(('render_pdf_work', work, page_format))
        return ['work.pdf']

    def render_remedial_latex(self, variant, content_config, page_format='A4'):
        self.calls.append(('render_remedial_latex', variant, page_format))
        return ['remedial.tex']

    def render_remedial_html(self, variant, content_config):
        self.calls.append(('render_remedial_html', variant))
        return ['remedial.html']

    def render_remedial_pdf(self, variant, content_config, page_format='A4'):
        self.calls.append(('render_remedial_pdf', variant, page_format))
        return ['remedial.pdf']


class FakeRenderedDocumentFileStore:
    def __init__(self):
        self.path_requests = []

    def document_from_paths(self, file_type, file_paths):
        self.path_requests.append((file_type, file_paths))
        return GeneratedDocument(file_type=file_type)
