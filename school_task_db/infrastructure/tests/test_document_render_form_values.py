from unittest import TestCase

from core_logic.value_objects.document_render_options import (
    WorkDocumentPrintOverrides,
)
from infrastructure.forms.document_rendering import (
    remedial_sheet_build_options_from_data,
    render_target_from_data,
    renderer_type_from_data,
    work_print_overrides_from_data,
)


class DocumentRenderFormValueTests(TestCase):
    def test_builds_render_target(self):
        target = render_target_from_data({
            'renderer_type': 'html',
            'format': 'A5',
        })

        self.assertEqual(target.renderer_type, 'html')
        self.assertEqual(target.page_format, 'A5')

    def test_render_target_uses_defaults(self):
        target = render_target_from_data({}, default_renderer_type='html')

        self.assertEqual(target.renderer_type, 'html')
        self.assertEqual(target.page_format, 'A4')

    def test_legacy_content_fields_do_not_change_work_overrides(self):
        overrides = work_print_overrides_from_data({
            'renderer_type': 'html',
            'format': 'A5',
            'answer_type': 'with_full_solutions',
            'include_hints': '1',
            'include_instructions': '1',
        })

        self.assertEqual(overrides, WorkDocumentPrintOverrides())

    def test_builds_temporary_work_overrides(self):
        overrides = work_print_overrides_from_data({
            'hide_theory': '1',
            'hide_text': '1',
            'hide_blank_cells': '1',
            'append_answers': '1',
            'break_between_variants': '0',
        })

        self.assertEqual(
            overrides,
            WorkDocumentPrintOverrides(
                hide_theory=True,
                hide_text=True,
                hide_blank_cells=True,
                append_answers=True,
                break_between_variants=False,
            ),
        )

    def test_builds_remedial_sheet_options_without_target_fields(self):
        options = remedial_sheet_build_options_from_data({
            'renderer_type': 'html',
            'format': 'A5',
            'answer_type': 'with_answers',
        })

        self.assertEqual(options.answer_type, 'with_answers')

    def test_renderer_type_defaults_to_pdf(self):
        self.assertEqual(renderer_type_from_data({}), 'pdf')
