from unittest import TestCase

from core_logic.value_objects.document_render_options import (
    FILE_TYPE_LABELS,
    RemedialSheetPrintOptions,
    RenderTarget,
    SUPPORTED_DOCUMENT_RENDERER_TYPES,
    WorkDocumentPrintOverrides,
    is_supported_document_renderer_type,
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

    def test_work_print_overrides_expose_hidden_content_types(self):
        overrides = WorkDocumentPrintOverrides(
            hide_theory=True,
            hide_text=True,
        )

        self.assertEqual(
            overrides.hidden_content_types,
            ('theory', 'text'),
        )

    def test_remedial_sheet_print_options_expose_section_flags(self):
        options = RemedialSheetPrintOptions(
            answer_type='with_full_solutions',
        )

        self.assertTrue(options.include_answers)
        self.assertTrue(options.include_short_solutions)
        self.assertTrue(options.include_full_solutions)

    def test_answer_only_print_options_do_not_add_solutions(self):
        options = RemedialSheetPrintOptions(answer_type='with_answers')

        self.assertTrue(options.include_answers)
        self.assertFalse(options.include_short_solutions)
        self.assertFalse(options.include_full_solutions)
