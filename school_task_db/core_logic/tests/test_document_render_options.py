from unittest import TestCase

from core_logic.value_objects.document_render_options import (
    FILE_TYPE_LABELS,
    RemedialSheetDocumentRenderOptions,
    RemedialSheetBuildOptions,
    RenderTarget,
    SUPPORTED_DOCUMENT_RENDERER_TYPES,
    WorkDocumentPrintOverrides,
    WorkDocumentRenderOptions,
    build_render_target,
    build_render_target_from_data,
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

    def test_build_render_target_from_legacy_arguments(self):
        target = build_render_target(renderer_type='html', pdf_format='A5')

        self.assertEqual(target.renderer_type, 'html')
        self.assertEqual(target.page_format, 'A5')

    def test_build_render_target_preserves_existing_target(self):
        existing_target = RenderTarget(renderer_type='latex', page_format='A4')

        target = build_render_target(
            renderer_type='html',
            pdf_format='A5',
            render_target=existing_target,
        )

        self.assertEqual(target, existing_target)

    def test_build_render_target_from_data(self):
        target = build_render_target_from_data({
            'renderer_type': 'html',
            'format': 'A5',
        })

        self.assertEqual(target.renderer_type, 'html')
        self.assertEqual(target.page_format, 'A5')

    def test_build_render_target_from_data_uses_default_renderer(self):
        target = build_render_target_from_data({}, default_renderer_type='html')

        self.assertEqual(target.renderer_type, 'html')
        self.assertEqual(target.page_format, 'A4')

    def test_builds_default_work_render_options(self):
        options = build_work_render_options({})

        self.assertEqual(options.renderer_type, 'pdf')
        self.assertEqual(options.pdf_format, 'A4')
        self.assertEqual(
            options.print_overrides,
            WorkDocumentPrintOverrides(),
        )
        self.assertEqual(options.content_description, 'по спецификации')

    def test_work_render_options_can_wrap_target_and_print_overrides(self):
        options = WorkDocumentRenderOptions(
            render_target=RenderTarget(renderer_type='html', page_format='A5'),
            print_overrides=WorkDocumentPrintOverrides(
                append_answers=True,
                break_between_variants=False,
            ),
        )

        self.assertEqual(options.renderer_type, 'html')
        self.assertEqual(options.pdf_format, 'A5')
        self.assertFalse(options.break_between_variants)
        self.assertEqual(
            options.content_description,
            'по спецификации + ответы в конце',
        )

    def test_legacy_content_fields_do_not_change_work_render_options(self):
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
        self.assertEqual(options.content_description, 'по спецификации')
        self.assertEqual(options.print_overrides, WorkDocumentPrintOverrides())

    def test_builds_temporary_work_print_overrides(self):
        options = build_work_render_options({
            'hide_theory': '1',
            'hide_text': '1',
            'hide_blank_cells': '1',
            'append_answers': '1',
        })

        self.assertEqual(
            options.print_overrides,
            WorkDocumentPrintOverrides(
                hide_theory=True,
                hide_text=True,
                hide_blank_cells=True,
                append_answers=True,
                break_between_variants=True,
            ),
        )
        self.assertEqual(
            options.print_overrides.hidden_content_types,
            ('theory', 'text'),
        )
        self.assertEqual(
            options.content_description,
            'по спецификации + ответы в конце',
        )

    def test_can_disable_work_variant_page_breaks_from_data(self):
        options = build_work_render_options({
            'break_between_variants': '0',
        })

        self.assertFalse(options.break_between_variants)
        self.assertFalse(
            options.print_overrides.break_between_variants,
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
