from django.test import SimpleTestCase

from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)
from core_logic.value_objects.document_section_catalog import (
    get_document_section_catalog,
)
from infrastructure.services.sectioned_document_renderer_specs import (
    sectioned_html_renderer_specs,
    sectioned_latex_renderer_specs,
)


class SectionedDocumentRendererSpecsTests(SimpleTestCase):
    def test_html_specs_cover_renderable_section_catalog(self):
        self.assertEqual(
            _renderer_section_types(
                sectioned_html_renderer_specs(),
                WORK_DOCUMENT_TYPE,
            ),
            _renderable_section_types(WORK_DOCUMENT_TYPE),
        )
        self.assertEqual(
            _renderer_section_types(
                sectioned_html_renderer_specs(),
                REMEDIAL_SHEET_DOCUMENT_TYPE,
            ),
            _renderable_section_types(REMEDIAL_SHEET_DOCUMENT_TYPE),
        )

    def test_latex_specs_cover_renderable_section_catalog(self):
        self.assertEqual(
            _renderer_section_types(
                sectioned_latex_renderer_specs(),
                WORK_DOCUMENT_TYPE,
            ),
            _renderable_section_types(WORK_DOCUMENT_TYPE),
        )
        self.assertEqual(
            _renderer_section_types(
                sectioned_latex_renderer_specs(),
                REMEDIAL_SHEET_DOCUMENT_TYPE,
            ),
            _renderable_section_types(REMEDIAL_SHEET_DOCUMENT_TYPE),
        )


def _renderable_section_types(document_type):
    return {
        section.section_type
        for section in get_document_section_catalog(
            document_type=document_type,
            include_legacy=True,
            renderable_only=True,
        )
    }


def _renderer_section_types(renderer_specs, document_type):
    for renderer_spec in renderer_specs:
        if renderer_spec.document_type == document_type:
            return set(renderer_spec.section_templates)
    return set()
