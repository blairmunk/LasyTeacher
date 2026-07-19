from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from infrastructure.services.legacy_document_file_renderer import (
    LegacyDocumentFileRenderer,
)


class FakeWorkGenerator:
    instances = []

    def __init__(self, output_dir):
        self.output_dir = output_dir
        self._content_config = None
        self.calls = []
        FakeWorkGenerator.instances.append(self)

    def generate(self, work):
        self.calls.append(('generate', work))
        return ['tasks-only.html']

    def generate_with_answers(self, work):
        self.calls.append(('generate_with_answers', work))
        return ['with-answers.html']


class LegacyDocumentFileRendererTests(TestCase):
    def setUp(self):
        FakeWorkGenerator.instances = []

    def test_render_html_work_uses_tasks_only_generator_by_default(self):
        renderer = LegacyDocumentFileRenderer()
        content_config = self._content_config()

        with patch(
            'html_generator.generators.work_generator.WorkHtmlGenerator',
            FakeWorkGenerator,
        ):
            files = renderer.render_html_work('work-object', content_config)

        generator = FakeWorkGenerator.instances[0]
        self.assertEqual(files, ['tasks-only.html'])
        self.assertEqual(generator.output_dir, 'web_html_output')
        self.assertEqual(generator.calls, [('generate', 'work-object')])
        self.assertIs(generator._content_config, content_config)

    def test_render_html_work_uses_answers_generator_when_needed(self):
        renderer = LegacyDocumentFileRenderer()
        content_config = self._content_config(include_answers=True)

        with patch(
            'html_generator.generators.work_generator.WorkHtmlGenerator',
            FakeWorkGenerator,
        ):
            files = renderer.render_html_work('work-object', content_config)

        generator = FakeWorkGenerator.instances[0]
        self.assertEqual(files, ['with-answers.html'])
        self.assertEqual(
            generator.calls,
            [('generate_with_answers', 'work-object')],
        )

    def test_render_latex_work_sets_page_format_for_legacy_generator(self):
        renderer = LegacyDocumentFileRenderer()
        content_config = self._content_config()

        with patch(
            'latex_generator.generators.work_generator.WorkLatexGenerator',
            FakeWorkGenerator,
        ):
            files = renderer.render_latex_work(
                'work-object',
                content_config,
                page_format='A5',
            )

        generator = FakeWorkGenerator.instances[0]
        self.assertEqual(files, ['tasks-only.html'])
        self.assertEqual(generator.output_dir, 'web_latex_output')
        self.assertEqual(generator._content_config['page_format'], 'A5')

    def test_render_remedial_html_uses_configured_template_and_output_dir(self):
        use_case = FakeRemedialSheetDataUseCase()
        template_calls = []

        def template_renderer(template_name, context):
            template_calls.append((template_name, context))
            return '<html>remedial</html>'

        with TemporaryDirectory() as output_dir:
            renderer = LegacyDocumentFileRenderer(
                get_remedial_sheet_data_use_case=use_case,
                template_renderer=template_renderer,
                html_output_dir=output_dir,
            )
            files = renderer.render_remedial_html(
                SimpleNamespace(pk='variant-1'),
                self._content_config(
                    include_short_solutions=True,
                    include_full_solutions=True,
                    include_answers=True,
                ),
            )

            output_path = Path(output_dir) / 'remedial_student-short.html'
            self.assertEqual(files, [str(output_path)])
            self.assertEqual(
                output_path.read_text(encoding='utf-8'),
                '<html>remedial</html>',
            )

        self.assertEqual(use_case.variant_id, 'variant-1')
        template_name, context = template_calls[0]
        self.assertEqual(template_name, 'works/remedial_sheet_print.html')
        self.assertEqual(context['variant'], 'variant-view')
        self.assertTrue(context['show_solutions'])
        self.assertTrue(context['show_full_solutions'])
        self.assertTrue(context['show_answers'])

    def test_render_pdf_files_from_html_uses_configured_output_dir(self):
        with TemporaryDirectory() as output_dir:
            renderer = LegacyDocumentFileRenderer(
                pdf_output_dir=output_dir,
            )
            pdf_generator = FakePdfGenerator()

            files = renderer._render_pdf_files_from_html(
                html_files=['/tmp/work.html'],
                pdf_generator=pdf_generator,
            )

            expected_pdf = Path(output_dir) / 'work.pdf'
            self.assertEqual(files, [str(expected_pdf)])
            self.assertEqual(
                pdf_generator.calls,
                [(Path('/tmp/work.html'), expected_pdf)],
            )

    def _content_config(self, **overrides):
        return {
            'include_answers': False,
            'include_short_solutions': False,
            'include_full_solutions': False,
            **overrides,
        }


class FakeRemedialSheetDataUseCase:
    def __init__(self):
        self.variant_id = None

    def execute(self, variant_id):
        self.variant_id = variant_id
        return SimpleNamespace(
            variant='variant-view',
            student=SimpleNamespace(short_name='student-short'),
            source_work='source-work-view',
            mark='mark-view',
            original_tasks=['original-task'],
            new_tasks=['new-task'],
        )


class FakePdfGenerator:
    def __init__(self):
        self.calls = []

    def generate_pdf(self, html_path, pdf_path):
        self.calls.append((html_path, pdf_path))
        return pdf_path
