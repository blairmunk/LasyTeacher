from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from core_logic.entities.document import Document, DocumentSection
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    HEADER_SECTION,
    PAGE_BREAK_SECTION,
    SCORE_TABLE_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    THEORY_SECTION,
)
from core_logic.value_objects.document_render_requests import DocumentRenderRequest
from core_logic.value_objects.task_print_settings import (
    TASK_RENDER_MODE_WITH_FULL_SOLUTION,
)
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
                    PAGE_BREAK_SECTION: 'documents/latex/sections/page_break.tex',
                    SCORE_TABLE_SECTION: 'documents/latex/sections/score_table.tex',
                    ANSWERS_SECTION: 'documents/latex/sections/answers.tex',
                    THEORY_SECTION: 'documents/latex/sections/theory.tex',
                    BLANK_CELLS_SECTION: (
                        'documents/latex/sections/blank_cells.tex'
                    ),
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
                        section_type=THEORY_SECTION,
                        payload={
                            'blocks': [
                                {
                                    'topic_name': 'Динамика',
                                    'content': r'Формула \(F=ma\)',
                                    'subtopics': [],
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
                                            'full_solution': 'Подставим в формулу',
                                            'render_mode': (
                                                TASK_RENDER_MODE_WITH_FULL_SOLUTION
                                            ),
                                            'blank_cells_after': True,
                                            'blank_cells': {
                                                'columns': 3,
                                                'rows_range': range(2),
                                                'latex_cells': [
                                                    r'\rule{0pt}{6.0mm}',
                                                    '',
                                                    '',
                                                ],
                                            },
                                        },
                                    ],
                                },
                            ],
                        },
                    ),
                    DocumentSection(
                        section_type=PAGE_BREAK_SECTION,
                    ),
                    DocumentSection(
                        section_type=BLANK_CELLS_SECTION,
                        payload={
                            'title': 'Черновик',
                            'columns': 3,
                            'rows_range': range(2),
                            'latex_cells': [r'\rule{0pt}{6.0mm}', '', ''],
                        },
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
            self.assertIn(r'\section*{\centering Теоретическая справка}', latex)
            self.assertIn(r'Формула \(F=ma\)', latex)
            self.assertIn(r'\section*{ Вариант 1 }', latex)
            self.assertIn('Найдите силу', latex)
            self.assertIn('Подсказка: F = ma', latex)
            self.assertIn(r'\textbf{Решение.}', latex)
            self.assertIn('Подставим в формулу', latex)
            self.assertIn(r'\clearpage', latex)
            self.assertIn(r'\section*{\centering Черновик}', latex)
            self.assertIn(r'\begin{tabular}{|*{ 3 }{p{0.3cm}|}}', latex)
            self.assertIn(r'\rule{0pt}{6.0mm}', latex)
            self.assertIn(r'\section*{\centering Критерии оценивания}', latex)
            self.assertIn(r'5 & 85\% & 8,5', latex)
            self.assertIn(r'\section*{\centering Ответы}', latex)
            self.assertIn('10 Н', latex)
            self.assertIn(r'\section*{\centering Краткие решения}', latex)
