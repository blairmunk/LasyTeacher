from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_recipes import (
    HEADER_SECTION,
    PAGE_BREAK_SECTION,
    SCORE_TABLE_SECTION,
    TASK_LIST_SECTION,
    THEORY_SECTION,
)
from core_logic.value_objects.document_render_requests import DocumentRenderRequest
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
                    PAGE_BREAK_SECTION: 'documents/html/sections/page_break.html',
                    SCORE_TABLE_SECTION: 'documents/html/sections/score_table.html',
                    TASK_LIST_SECTION: 'documents/html/sections/task_list.html',
                    THEORY_SECTION: 'documents/html/sections/theory.html',
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
                        section_type=THEORY_SECTION,
                        payload={
                            'blocks': [
                                {
                                    'topic_name': 'Динамика',
                                    'content': 'Второй закон Ньютона',
                                    'subtopics': [],
                                },
                            ],
                        },
                    ),
                    DocumentSection(
                        section_type=PAGE_BREAK_SECTION,
                    ),
                    DocumentSection(
                        section_type=SCORE_TABLE_SECTION,
                        payload={
                            'max_score': 10,
                            'criteria': [
                                {
                                    'score': 5,
                                    'min_percent': 85,
                                    'min_points': 8.5,
                                },
                            ],
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
            self.assertIn('Теоретическая справка', html)
            self.assertIn('Второй закон Ньютона', html)
            self.assertIn('page-break-after: always', html)
            self.assertIn('Критерии оценивания', html)
            self.assertIn('<td>85%</td>', html)
            self.assertIn('Вариант 1', html)
            self.assertIn('Найдите силу', html)
            self.assertIn('Подсказка: F = ma', html)
