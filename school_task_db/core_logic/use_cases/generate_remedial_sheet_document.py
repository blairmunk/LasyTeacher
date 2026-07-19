"""Backward-compatible imports for remedial sheet document rendering."""

from core_logic.use_cases.render_remedial_sheet_document import (
    RenderRemedialSheetDocumentRequest,
    RenderRemedialSheetDocumentUseCase,
    SUPPORTED_REMEDIAL_SHEET_RENDERER_TYPES,
)


GenerateRemedialSheetDocumentRequest = RenderRemedialSheetDocumentRequest
GenerateRemedialSheetDocumentUseCase = RenderRemedialSheetDocumentUseCase
SUPPORTED_REMEDIAL_SHEET_GENERATOR_TYPES = SUPPORTED_REMEDIAL_SHEET_RENDERER_TYPES
