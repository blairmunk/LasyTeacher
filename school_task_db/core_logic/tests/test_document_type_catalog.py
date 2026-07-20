from unittest import TestCase

from core_logic.entities.document import (
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.use_cases.get_document_type_catalog import (
    GetDocumentTypeCatalogRequest,
    GetDocumentTypeCatalogUseCase,
)
from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)
from core_logic.value_objects.document_type_catalog import (
    get_document_type_catalog,
    validate_document_type,
)


class DocumentTypeCatalogTests(TestCase):
    def test_lists_all_supported_document_types(self):
        document_types = get_document_type_catalog()

        type_keys = [item.document_type for item in document_types]

        self.assertIn(WORK_DOCUMENT_TYPE, type_keys)
        self.assertIn(REMEDIAL_SHEET_DOCUMENT_TYPE, type_keys)
        self.assertIn(WORKSHEET_DOCUMENT_TYPE, type_keys)

    def test_can_return_renderable_document_types_only(self):
        document_types = get_document_type_catalog(renderable_only=True)

        type_keys = [item.document_type for item in document_types]

        self.assertEqual(
            type_keys,
            [WORK_DOCUMENT_TYPE, REMEDIAL_SHEET_DOCUMENT_TYPE],
        )

    def test_exposes_source_types_for_renderable_documents(self):
        document_types = get_document_type_catalog(renderable_only=True)
        source_types = {
            item.document_type: item.source_type
            for item in document_types
        }

        self.assertEqual(source_types[WORK_DOCUMENT_TYPE], WORK_SOURCE_TYPE)
        self.assertEqual(
            source_types[REMEDIAL_SHEET_DOCUMENT_TYPE],
            REMEDIAL_VARIANT_SOURCE_TYPE,
        )

    def test_validates_supported_document_type(self):
        validate_document_type(WORKSHEET_DOCUMENT_TYPE)

    def test_rejects_unknown_document_type(self):
        with self.assertRaises(ValueError):
            validate_document_type('unknown_document_type')


class GetDocumentTypeCatalogUseCaseTests(TestCase):
    def test_returns_document_type_catalog(self):
        data = GetDocumentTypeCatalogUseCase().execute(
            GetDocumentTypeCatalogRequest(renderable_only=True),
        )

        self.assertEqual(
            [item.document_type for item in data.document_types],
            [WORK_DOCUMENT_TYPE, REMEDIAL_SHEET_DOCUMENT_TYPE],
        )
