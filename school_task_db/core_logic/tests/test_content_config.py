from unittest import TestCase

from core_logic.value_objects.content_config import (
    FILE_TYPE_LABELS,
    RemedialSheetDocumentRenderOptions,
    RemedialSheetBuildOptions,
    RenderTarget,
    SUPPORTED_DOCUMENT_RENDERER_TYPES,
    WorkDocumentBuildOptions,
    WorkDocumentRenderOptions,
    build_remedial_sheet_render_options,
    build_work_render_options,
    is_supported_document_renderer_type,
    renderer_type_from_data,
)


class DocumentRenderOptionsTests(TestCase):
    def test_supported_renderer_types_match_file_type_labels(self):
        self.assertEqual(
            SUPPORTED_DOCUMENT_RENDERER_TYPES,
            frozenset(FILE_TYPE_LABELS),
        )

    def test_checks_supported_renderer_type(self):
        self.assertTrue(is_supported_document_renderer_type('pdf'))
        self.assertTrue(is_supported_document_renderer_type('html'))
        self.assertFalse(is_supported_document_renderer_type('docx'))

    def test_render_target_exposes_file_type_label(self):
        target = RenderTarget(renderer_type='html', page_format='A5')

        self.assertEqual(target.renderer_type, 'html')
        self.assertEqual(target.page_format, 'A5')
        self.assertEqual(target.file_type_label, 'HTML')

    def test_builds_default_work_render_options(self):
        options = build_work_render_options({})

        self.assertEqual(options.renderer_type, 'pdf')
        self.assertEqual(options.pdf_format, 'A4')
        self.assertEqual(options.answer_type, 'tasks_only')
        self.assertEqual(options.content_description, 'только задания')
        self.assertEqual(
            options.content_config,
            {
                'include_answers': False,
                'include_short_solutions': False,
                'include_full_solutions': False,
                'answer_type': 'tasks_only',
                'include_hints': False,
                'include_instructions': False,
            },
        )

    def test_work_render_options_can_wrap_target_and_build_options(self):
        options = WorkDocumentRenderOptions(
            render_target=RenderTarget(renderer_type='html', page_format='A5'),
            build_options=WorkDocumentBuildOptions(
                answer_type='with_answers',
                include_hints=True,
            ),
        )

        self.assertEqual(options.renderer_type, 'html')
        self.assertEqual(options.pdf_format, 'A5')
        self.assertEqual(options.answer_type, 'with_answers')
        self.assertTrue(options.include_hints)
        self.assertFalse(options.include_instructions)
        self.assertEqual(options.content_description, 'с ответами + подсказки')

    def test_supports_legacy_with_answers_flag(self):
        options = build_work_render_options({
            'answer_type': 'tasks_only',
            'with_answers': '1',
        })

        self.assertEqual(options.answer_type, 'with_answers')
        self.assertEqual(options.content_description, 'с ответами')
        self.assertTrue(options.content_config['include_answers'])

    def test_builds_full_solution_work_render_options(self):
        options = build_work_render_options({
            'renderer_type': 'html',
            'format': 'A5',
            'answer_type': 'with_full_solutions',
            'include_hints': '1',
            'include_instructions': '1',
        })

        self.assertEqual(options.renderer_type, 'html')
        self.assertEqual(options.file_type_label, 'HTML')
        self.assertEqual(options.render_target.renderer_type, 'html')
        self.assertEqual(options.render_target.page_format, 'A5')
        self.assertEqual(options.pdf_format, 'A5')
        self.assertEqual(
            options.content_description,
            'с полными решениями + подсказки + инструкции',
        )
        self.assertEqual(
            options.content_config,
            {
                'include_answers': True,
                'include_short_solutions': True,
                'include_full_solutions': True,
                'answer_type': 'with_full_solutions',
                'include_hints': True,
                'include_instructions': True,
            },
        )

    def test_builds_default_remedial_sheet_render_options(self):
        options = build_remedial_sheet_render_options({})

        self.assertEqual(options.renderer_type, 'pdf')
        self.assertEqual(options.render_target.renderer_type, 'pdf')
        self.assertEqual(options.render_target.page_format, 'A4')
        self.assertEqual(options.pdf_format, 'A4')
        self.assertEqual(options.answer_type, 'with_short_solutions')
        self.assertEqual(
            options.content_config,
            {
                'include_answers': True,
                'include_short_solutions': True,
                'include_full_solutions': False,
                'page_format': 'A4',
            },
        )

    def test_remedial_sheet_render_options_can_wrap_target_and_build_options(self):
        options = RemedialSheetDocumentRenderOptions(
            render_target=RenderTarget(renderer_type='latex', page_format='A5'),
            build_options=RemedialSheetBuildOptions(
                answer_type='with_full_solutions',
            ),
        )

        self.assertEqual(options.renderer_type, 'latex')
        self.assertEqual(options.pdf_format, 'A5')
        self.assertEqual(options.answer_type, 'with_full_solutions')
        self.assertEqual(
            options.content_config,
            {
                'include_answers': True,
                'include_short_solutions': True,
                'include_full_solutions': True,
                'page_format': 'A5',
            },
        )

    def test_builds_work_options_from_renderer_type(self):
        options = build_work_render_options({
            'renderer_type': 'html',
        })

        self.assertEqual(options.renderer_type, 'html')

    def test_builds_remedial_sheet_options_from_renderer_type(self):
        options = build_remedial_sheet_render_options({
            'renderer_type': 'html',
        })

        self.assertEqual(options.renderer_type, 'html')

    def test_renderer_type_defaults_to_pdf(self):
        self.assertEqual(renderer_type_from_data({}), 'pdf')

    def test_renderer_type_uses_configured_default(self):
        self.assertEqual(renderer_type_from_data({}, default='html'), 'html')
