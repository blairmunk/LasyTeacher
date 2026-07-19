from unittest import TestCase

from core_logic.entities.document import Document, DocumentSourceRef
from core_logic.services.document_renderer_registry import UnsupportedDocumentRenderer
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_render_plan import DocumentRenderRequest
from infrastructure.services.document_renderer_registry_factory import (
    build_legacy_document_renderer_registry,
)


class DocumentRendererRegistryFactoryTests(TestCase):
    def test_builds_registry_for_work_and_remedial_renderers(self):
        registry = self._build_registry()

        for document_type in ('work', 'remedial_sheet'):
            for renderer_type in ('latex', 'html', 'pdf'):
                renderer = registry.get(
                    renderer_type=renderer_type,
                    document_type=document_type,
                )

                self.assertIsNotNone(renderer)

    def test_builds_registry_without_cross_document_fallback(self):
        registry = self._build_registry()

        with self.assertRaises(UnsupportedDocumentRenderer):
            registry.get(renderer_type='html', document_type='worksheet')

    def test_registered_work_renderer_uses_configured_source_getter(self):
        requests = []
        registry = self._build_registry(
            get_work_source=lambda source_id: f'work:{source_id}',
            render_html_work_files=lambda work, config: requests.append(work) or [],
        )
        renderer = registry.get(renderer_type='html', document_type='work')

        renderer.render(DocumentRenderRequest(
            document=Document(
                title='Контрольная',
                source=DocumentSourceRef(
                    source_type='work',
                    source_id='work-1',
                ),
            ),
            render_target=RenderTarget(renderer_type='html'),
        ))

        self.assertEqual(requests, ['work:work-1'])

    def _build_registry(
        self,
        get_work_source=lambda source_id: f'work:{source_id}',
        get_remedial_source=lambda source_id: f'variant:{source_id}',
        render_latex_work_files=lambda work, config, page_format: [],
        render_html_work_files=lambda work, config: [],
        render_pdf_work_files=lambda work, config, page_format: [],
        render_remedial_latex_files=lambda variant, config, page_format: [],
        render_remedial_html_files=lambda variant, config: [],
        render_remedial_pdf_files=lambda variant, config, page_format: [],
    ):
        return build_legacy_document_renderer_registry(
            document_from_paths=lambda file_type, file_paths: None,
            get_work_source=get_work_source,
            get_remedial_source=get_remedial_source,
            render_latex_work_files=render_latex_work_files,
            render_html_work_files=render_html_work_files,
            render_pdf_work_files=render_pdf_work_files,
            render_remedial_latex_files=render_remedial_latex_files,
            render_remedial_html_files=render_remedial_html_files,
            render_remedial_pdf_files=render_remedial_pdf_files,
        )
