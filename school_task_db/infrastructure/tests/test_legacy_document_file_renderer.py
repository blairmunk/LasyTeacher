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
        renderer = LegacyDocumentFileRenderer(
            get_remedial_sheet_data_use_case=None,
        )
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
        renderer = LegacyDocumentFileRenderer(
            get_remedial_sheet_data_use_case=None,
        )
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
        renderer = LegacyDocumentFileRenderer(
            get_remedial_sheet_data_use_case=None,
        )
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

    def _content_config(self, **overrides):
        return {
            'include_answers': False,
            'include_short_solutions': False,
            'include_full_solutions': False,
            **overrides,
        }
