from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    HEADER_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
)
from core_logic.value_objects.document_render_requests import DocumentRenderRequest
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)
from infrastructure.services.sectioned_document_renderer_factory import (
    build_template_sectioned_text_document_renderer,
)


class SectionedDocumentLatexTemplateTests(SimpleTestCase):
    def test_renders_sectioned_work_document_to_latex_file(self):
        with TemporaryDirectory() as output_dir:
            renderer = build_template_sectioned_text_document_renderer(
                renderer_type='latex',
                section_templates={
                    HEADER_SECTION: 'documents/latex/sections/header.tex',
                    TASK_LIST_SECTION: 'documents/latex/sections/task_list.tex',
                    ANSWERS_SECTION: 'documents/latex/sections/answers.tex',
                    SHORT_SOLUTIONS_SECTION: (
                        'documents/latex/sections/short_solutions.tex'
                    ),
                },
                filename_builder=lambda request: 'work.tex',
                file_store=RenderedDocumentFileStore(
                    output_dirs={'latex': output_dir},
                ),
                wrapper_template_name='documents/latex/base/document.tex',
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
                                    'duration': 45,
                                    'max_score': 10,
                                    'tasks': [
                                        {
                                            'order': 1,
                                            'text': 'Найдите силу',
                                            'hint': 'F = ma',
                                            'max_points': 2,
                                            'answer': '10 Н',
                                            'short_solution': 'F = ma',
                                        },
                                    ],
                                },
                            ],
                        },
                    ),
                    DocumentSection(
                        section_type=ANSWERS_SECTION,
                        payload={
                            'variants': [
                                {
                                    'title': 'Вариант 1',
                                    'tasks': [{'answer': '10 Н'}],
                                },
                            ],
                        },
                    ),
                    DocumentSection(
                        section_type=SHORT_SOLUTIONS_SECTION,
                        payload={
                            'variants': [
                                {
                                    'title': 'Вариант 1',
                                    'tasks': [
                                        {
                                            'order': 1,
                                            'short_solution': 'F = ma',
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
                    render_target=RenderTarget(renderer_type='latex'),
                )
            )

            latex = (Path(output_dir) / 'work.tex').read_text(encoding='utf-8')
            self.assertEqual(result.file_type, 'latex')
            self.assertEqual(result.files[0].filename, 'work.tex')
            self.assertIn(r'\documentclass', latex)
            self.assertIn(r'\begin{document}', latex)
            self.assertIn(r'{\LARGE\bfseries Контрольная}', latex)
            self.assertIn(r'\section*{ Вариант 1 }', latex)
            self.assertIn('Найдите силу', latex)
            self.assertIn('Подсказка: F = ma', latex)
            self.assertIn(r'\section*{\centering Ответы}', latex)
            self.assertIn('10 Н', latex)
            self.assertIn(r'\section*{\centering Краткие решения}', latex)
