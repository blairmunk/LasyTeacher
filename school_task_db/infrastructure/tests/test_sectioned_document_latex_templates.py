from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from core_logic.entities.document import (
    Document,
    DocumentPresentation,
    DocumentSection,
)
from core_logic.value_objects.document_render_options import RenderTarget
from core_logic.value_objects.document_recipes import (
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    PAGE_BREAK_SECTION,
    SCORE_TABLE_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
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
                    BLANK_CELLS_SECTION: (
                        'documents/latex/sections/blank_cells.tex'
                    ),
                    SHORT_SOLUTIONS_SECTION: (
                        'documents/latex/sections/short_solutions.tex'
                    ),
                    FULL_SOLUTIONS_SECTION: (
                        'documents/latex/sections/full_solutions.tex'
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
                presentation=DocumentPresentation(
                    custom_latex_preamble=(
                        r'\renewenvironment{schooltheory}'
                        r'{\begin{quote}}{\end{quote}}'
                    ),
                ),
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
                                    'print_blocks': [
                                        {
                                            'block_type': 'theory',
                                            'title': 'Теория варианта',
                                            'content': {
                                                'topics': [
                                                    {
                                                        'name': 'Импульс',
                                                        'content': (
                                                            'Импульс сохраняется'
                                                        ),
                                                        'subtopics': [],
                                                    },
                                                ],
                                            },
                                        },
                                        {
                                            'block_type': 'task',
                                            'task': {
                                                'order': 1,
                                                'text': 'Найдите силу',
                                                'latex_content': (
                                                    'Найдите силу'
                                                ),
                                                'hint': 'F = ma',
                                                'max_points': 2,
                                                'answer': '10 Н',
                                                'short_solution': 'F = ma',
                                                'full_solution': (
                                                    'Подставим в формулу'
                                                ),
                                                'render_mode': (
                                                    TASK_RENDER_MODE_WITH_FULL_SOLUTION
                                                ),
                                            },
                                        },
                                        {
                                            'block_type': 'text',
                                            'title': 'Самопроверка',
                                            'content': {
                                                'body': (
                                                    'Проверьте единицы измерения'
                                                ),
                                            },
                                        },
                                        {
                                            'block_type': 'blank_cells',
                                            'blank_cells': {
                                                'rows': 2,
                                                'columns': 3,
                                                'latex_cell_size_mm': '4.0',
                                            },
                                        },
                                    ],
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
                                                'rows': 2,
                                                'columns': 3,
                                                'latex_cell_size_mm': '4.0',
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
                            'rows': 2,
                            'columns': 3,
                            'latex_cell_size_mm': '4.0',
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
                        title='Ключ для самопроверки',
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
                    DocumentSection(
                        section_type=FULL_SOLUTIONS_SECTION,
                        payload={
                            'variants': [
                                {
                                    'title': 'Вариант 1',
                                    'tasks': [
                                        {
                                            'order': 1,
                                            'full_solution': (
                                                'Подставим в формулу'
                                            ),
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
            self.assertIn(r'\newenvironment{schooltheory}', latex)
            self.assertIn(r'\begin{tcolorbox}', latex)
            self.assertIn(
                (
                    r'\renewenvironment{schooltheory}'
                    r'{\begin{quote}}{\end{quote}}'
                ),
                latex,
            )
            self.assertIn(r'\begin{document}', latex)
            self.assertIn(r'\begin{schoolheader}', latex)
            self.assertIn(r'\begin{schooltheory}', latex)
            self.assertIn(r'\end{schooltheory}', latex)
            self.assertIn(r'\begin{schooltasklist}', latex)
            self.assertIn(r'\begin{schoolpagebreak}', latex)
            self.assertIn(r'\begin{schoolblankcells}', latex)
            self.assertIn(r'\usepackage{tikz}', latex)
            self.assertIn(r'\newcommand{\schoolgrid}[3]', latex)
            self.assertIn(r'\schoolgridcell=\linewidth', latex)
            self.assertIn(r'\advance\schoolgridcell by -0.2pt', latex)
            self.assertIn(r'\divide\schoolgridcell by #2', latex)
            self.assertIn(r'\begin{schoolscoretable}', latex)
            self.assertIn(r'\begin{schoolanswers}', latex)
            self.assertIn(r'\begin{schoolshortsolutions}', latex)
            self.assertIn(r'\begin{schoolfullsolutions}', latex)
            self.assertNotIn(r'\newpage', latex)
            self.assertLess(
                latex.index(r'\newenvironment{schooltheory}'),
                latex.index(r'\renewenvironment{schooltheory}'),
            )
            self.assertLess(
                latex.index(r'\renewenvironment{schooltheory}'),
                latex.index(r'\begin{schooltheory}'),
            )
            self.assertIn(r'\Large\sffamily\bfseries Контрольная', latex)
            self.assertIn(r'\schoolvariantheading{ Вариант 1 }', latex)
            self.assertIn(r'\schoolsubheading{ Теория варианта }', latex)
            self.assertIn('Импульс сохраняется', latex)
            self.assertIn(r'\schoolsubheading{ Самопроверка }', latex)
            self.assertIn('Проверьте единицы измерения', latex)
            self.assertIn('Найдите силу', latex)
            self.assertIn('Подсказка: F = ma', latex)
            self.assertIn(r'\textbf{Решение.}', latex)
            self.assertIn('Подставим в формулу', latex)
            self.assertIn(r'\clearpage', latex)
            self.assertIn(r'\schoolsectionheading{ Черновик }', latex)
            self.assertEqual(
                latex.count(r'\schoolgrid{ 2 }{ 3 }{ 4.0 }'),
                2,
            )
            self.assertNotIn(r'\begin{tabular}{|*{ 3 }', latex)
            self.assertIn(r'\schoolsectionheading{ Критерии оценивания }', latex)
            self.assertIn(r'5 & 85\% & 8,5', latex)
            self.assertIn(
                r'\schoolsectionheading{ Ключ для самопроверки }',
                latex,
            )
            self.assertIn('10 Н', latex)
            self.assertIn(r'\schoolsectionheading{ Краткие решения }', latex)

    def test_remedial_page_breaks_and_titles_are_recipe_driven(self):
        with TemporaryDirectory() as output_dir:
            renderer = build_template_sectioned_text_document_renderer(
                renderer_type='latex',
                section_templates={
                    ORIGINAL_MISTAKES_SECTION: (
                        'documents/latex/sections/'
                        'remedial_original_mistakes.tex'
                    ),
                    PAGE_BREAK_SECTION: (
                        'documents/latex/sections/page_break.tex'
                    ),
                    TRAINING_TASKS_SECTION: (
                        'documents/latex/sections/'
                        'remedial_training_tasks.tex'
                    ),
                },
                filename_builder=lambda request: 'remedial.tex',
                file_store=RenderedDocumentFileStore(
                    output_dirs={'latex': output_dir},
                ),
                wrapper_template_name='documents/latex/base/document.tex',
            )
            document = Document(
                title='Работа над ошибками',
                document_type='remedial_sheet',
                sections=[
                    DocumentSection(
                        section_type=ORIGINAL_MISTAKES_SECTION,
                        title='Мои ошибки',
                        payload={'tasks': []},
                    ),
                    DocumentSection(section_type=PAGE_BREAK_SECTION),
                    DocumentSection(
                        section_type=TRAINING_TASKS_SECTION,
                        title='Повторная попытка',
                        payload={'tasks': []},
                    ),
                ],
            )

            renderer.render(
                DocumentRenderRequest(
                    document=document,
                    render_target=RenderTarget(renderer_type='latex'),
                )
            )
            latex = (Path(output_dir) / 'remedial.tex').read_text(
                encoding='utf-8',
            )

        self.assertIn(r'\schoolsectionheading{ Мои ошибки }', latex)
        self.assertIn(r'\schoolsectionheading{ Повторная попытка }', latex)
        self.assertEqual(latex.count(r'\clearpage'), 1)
        self.assertNotIn(r'\newpage', latex)
