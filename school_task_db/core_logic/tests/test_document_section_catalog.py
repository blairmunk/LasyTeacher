from unittest import TestCase

from core_logic.use_cases.get_document_section_catalog import (
    GetDocumentSectionCatalogRequest,
    GetDocumentSectionCatalogUseCase,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_DOCUMENT_TYPE,
    ANSWER_KEY_SECTION,
    HEADER_SECTION,
    LEGACY_TASK_VARIANTS_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
    THEORY_SECTION,
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)
from core_logic.value_objects.document_section_catalog import (
    get_document_section_catalog,
    validate_document_section_types,
)


class DocumentSectionCatalogTests(TestCase):
    def test_lists_sections_supported_by_document_type(self):
        sections = get_document_section_catalog(
            document_type=WORKSHEET_DOCUMENT_TYPE,
        )

        section_types = [section.section_type for section in sections]

        self.assertIn(HEADER_SECTION, section_types)
        self.assertIn(TASK_LIST_SECTION, section_types)
        self.assertIn(THEORY_SECTION, section_types)
        self.assertNotIn(ORIGINAL_MISTAKES_SECTION, section_types)

    def test_hides_legacy_sections_by_default(self):
        sections = get_document_section_catalog(
            document_type=WORK_DOCUMENT_TYPE,
        )

        section_types = [section.section_type for section in sections]

        self.assertNotIn(LEGACY_TASK_VARIANTS_SECTION, section_types)

    def test_can_include_legacy_sections(self):
        sections = get_document_section_catalog(
            document_type=WORK_DOCUMENT_TYPE,
            include_legacy=True,
        )

        section_types = [section.section_type for section in sections]

        self.assertIn(LEGACY_TASK_VARIANTS_SECTION, section_types)
        self.assertTrue(
            any(
                section.section_type == LEGACY_TASK_VARIANTS_SECTION
                and section.is_legacy
                for section in sections
            )
        )

    def test_answer_key_section_is_available_for_answer_key_documents(self):
        sections = get_document_section_catalog(
            document_type=ANSWER_KEY_DOCUMENT_TYPE,
        )

        section_types = [section.section_type for section in sections]

        self.assertIn(ANSWER_KEY_SECTION, section_types)

    def test_can_return_renderable_sections_only(self):
        sections = get_document_section_catalog(
            document_type=WORKSHEET_DOCUMENT_TYPE,
            renderable_only=True,
        )

        section_types = [section.section_type for section in sections]

        self.assertNotIn(THEORY_SECTION, section_types)
        self.assertNotIn(TASK_LIST_SECTION, section_types)

    def test_reports_section_renderability_for_document_type(self):
        sections = get_document_section_catalog(
            document_type=WORK_DOCUMENT_TYPE,
        )
        task_list_section = next(
            section
            for section in sections
            if section.section_type == TASK_LIST_SECTION
        )

        self.assertTrue(task_list_section.is_renderable_for(WORK_DOCUMENT_TYPE))
        self.assertFalse(
            task_list_section.is_renderable_for(WORKSHEET_DOCUMENT_TYPE),
        )

    def test_validates_supported_sections(self):
        validate_document_section_types(
            WORKSHEET_DOCUMENT_TYPE,
            [HEADER_SECTION, TASK_LIST_SECTION],
        )

    def test_rejects_unknown_sections(self):
        with self.assertRaises(ValueError):
            validate_document_section_types(
                WORKSHEET_DOCUMENT_TYPE,
                ['unknown_section'],
            )

    def test_rejects_sections_for_wrong_document_type(self):
        with self.assertRaises(ValueError):
            validate_document_section_types(
                WORKSHEET_DOCUMENT_TYPE,
                [ORIGINAL_MISTAKES_SECTION],
            )


class GetDocumentSectionCatalogUseCaseTests(TestCase):
    def test_returns_filtered_section_catalog(self):
        data = GetDocumentSectionCatalogUseCase().execute(
            GetDocumentSectionCatalogRequest(
                document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                renderable_only=True,
            ),
        )

        section_types = [section.section_type for section in data.sections]

        self.assertIn(ORIGINAL_MISTAKES_SECTION, section_types)
        self.assertNotIn(TASK_LIST_SECTION, section_types)
