from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_recipes import (
    HEADER_SECTION,
    TASK_LIST_SECTION,
)
from core_logic.value_objects.document_render_plan import DocumentRenderRequest
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_renderer_factory import (
    build_template_sectioned_text_document_renderer,
)


class SectionedDocumentHtmlTemplateTests(SimpleTestCase):
    def test_renders_sectioned_work_document_to_html_file(self):
        with TemporaryDirectory() as output_dir:
            renderer = build_template_sectioned_text_document_renderer(
                renderer_type='html',
                section_templates={
                    HEADER_SECTION: 'documents/html/sections/header.html',
                    TASK_LIST_SECTION: 'documents/html/sections/task_list.html',
                },
                filename_builder=lambda request: 'work.html',
                file_store=RenderedDocumentFileStore(
                    output_dirs={'html': output_dir},
                ),
                wrapper_template_name='documents/html/base/document.html',
            )
            document = Document(
                title='Контрольная',
                document_type='work',
                sections=[
                    DocumentSection(
                        section_type=HEADER_SECTION,
                        payload={
                            'title': 'Контрольная',
                            'duration': 45,
                            'max_score': 10,
                        },
                    ),
                    DocumentSection(
                        section_type=TASK_LIST_SECTION,
                        payload={
                            'include_hints': True,
                            'variants': [
                                {
                                    'title': 'Вариант 1',
                                    'tasks': [
                                        {
                                            'text': 'Найдите силу',
                                            'hint': 'F = ma',
                                            'instruction': '',
                                            'max_points': 2,
                                        },
                                    ],
                                },
                            ],
                        },
                    ),
                ],
            )

            result = renderer.render(
                DocumentRenderRequest(
                    document=document,
                    render_target=RenderTarget(renderer_type='html'),
                )
            )

            html = (Path(output_dir) / 'work.html').read_text(encoding='utf-8')
            self.assertEqual(result.file_type, 'html')
            self.assertEqual(result.files[0].filename, 'work.html')
            self.assertIn('<title>Контрольная</title>', html)
            self.assertIn('<h1>Контрольная</h1>', html)
            self.assertIn('Вариант 1', html)
            self.assertIn('Найдите силу', html)
            self.assertIn('Подсказка: F = ma', html)
