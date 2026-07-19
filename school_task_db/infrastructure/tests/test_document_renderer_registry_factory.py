from django.test import TestCase

from core_logic.services.document_renderer_registry import UnsupportedDocumentRenderer
from infrastructure.services.document_renderer_registry_factory import (
    build_legacy_document_renderer_registry,
)


class DocumentRendererRegistryFactoryTests(TestCase):
    def test_builds_registry_for_work_and_remedial_renderers(self):
        registry = build_legacy_document_renderer_registry(
            document_from_paths=lambda file_type, file_paths: None,
            generate_latex_work=lambda work, config, page_format: [],
            generate_html_work=lambda work, config: [],
            generate_pdf_work=lambda work, config, page_format: [],
            generate_remedial_latex=lambda variant, config, page_format: [],
            generate_remedial_html=lambda variant, config: [],
            generate_remedial_pdf=lambda variant, config, page_format: [],
        )

        for document_type in ('work', 'remedial_sheet'):
            for renderer_type in ('latex', 'html', 'pdf'):
                renderer = registry.get(
                    renderer_type=renderer_type,
                    document_type=document_type,
                )

                self.assertIsNotNone(renderer)

    def test_builds_registry_without_cross_document_fallback(self):
        registry = build_legacy_document_renderer_registry(
            document_from_paths=lambda file_type, file_paths: None,
            generate_latex_work=lambda work, config, page_format: [],
            generate_html_work=lambda work, config: [],
            generate_pdf_work=lambda work, config, page_format: [],
            generate_remedial_latex=lambda variant, config, page_format: [],
            generate_remedial_html=lambda variant, config: [],
            generate_remedial_pdf=lambda variant, config, page_format: [],
        )

        with self.assertRaises(UnsupportedDocumentRenderer):
            registry.get(renderer_type='html', document_type='worksheet')
