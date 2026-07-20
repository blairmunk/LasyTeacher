"""Render section-based document content into a generated text file."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable

from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.interfaces.document_rendering import IDocumentRenderer
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_render_plan import DocumentRenderRequest


class SectionedDocumentFileRenderer(IDocumentRenderer):
    def __init__(
        self,
        file_type: str,
        filename_builder: Callable[[DocumentRenderRequest], str],
        content_renderer,
        file_store,
    ):
        if not file_type:
            raise ValueError('file_type is required')

        self.file_type = file_type
        self.filename_builder = filename_builder
        self.content_renderer = content_renderer
        self.file_store = file_store

    def render(self, request: DocumentRenderRequest) -> GeneratedDocument:
        filename = self.filename_builder(request)
        if not filename:
            raise ValueError('filename is required')

        content = self.content_renderer.render_content(request)
        return self.file_store.write_text_document(
            file_type=self.file_type,
            filename=filename,
            content=content,
        )


class SectionedHtmlToPdfDocumentRenderer(IDocumentRenderer):
    def __init__(
        self,
        html_filename_builder: Callable[[DocumentRenderRequest], str],
        html_content_renderer,
        file_store,
        html_to_pdf_renderer_factory=None,
    ):
        self.html_filename_builder = html_filename_builder
        self.html_content_renderer = html_content_renderer
        self.file_store = file_store
        self.html_to_pdf_renderer_factory = (
            html_to_pdf_renderer_factory or self._default_html_to_pdf_renderer
        )

    def render(self, request: DocumentRenderRequest) -> GeneratedDocument:
        html_filename = self.html_filename_builder(request)
        if not html_filename:
            raise ValueError('filename is required')

        pdf_output_dir = self._pdf_output_dir()
        pdf_output_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_output_dir / Path(html_filename).with_suffix('.pdf').name

        with TemporaryDirectory() as temp_dir:
            html_path = Path(temp_dir) / html_filename
            html_path.parent.mkdir(parents=True, exist_ok=True)
            html_path.write_text(
                self.html_content_renderer.render_content(
                    self._html_request(request),
                ),
                encoding='utf-8',
            )
            html_to_pdf_renderer = self.html_to_pdf_renderer_factory(request)
            rendered_pdf = html_to_pdf_renderer.generate_pdf(html_path, pdf_path)

        return self.file_store.document_from_paths('pdf', [rendered_pdf])

    def _pdf_output_dir(self) -> Path:
        output_dir = getattr(self.file_store, 'output_dirs', {}).get('pdf')
        if not output_dir:
            raise ValueError('pdf output dir is required')
        return Path(output_dir)

    def _html_request(self, request: DocumentRenderRequest) -> DocumentRenderRequest:
        return DocumentRenderRequest(
            document=request.document,
            render_target=RenderTarget(
                renderer_type='html',
                page_format=request.render_target.page_format,
            ),
        )

    def _default_html_to_pdf_renderer(self, request):
        from infrastructure.services.html_to_pdf_renderer import (
            HtmlToPdfRenderer,
        )

        return HtmlToPdfRenderer(
            format=request.render_target.page_format,
            wait_for_mathjax=True,
        )
