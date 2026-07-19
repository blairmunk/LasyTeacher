"""Backward-compatible imports for work document rendering use cases."""

from core_logic.use_cases.render_work_document import (
    RenderWorkDocumentRequest,
    RenderWorkDocumentUseCase,
    SUPPORTED_WORK_RENDERER_TYPES,
)


GenerateWorkDocumentRequest = RenderWorkDocumentRequest
GenerateWorkDocumentUseCase = RenderWorkDocumentUseCase
SUPPORTED_WORK_GENERATOR_TYPES = SUPPORTED_WORK_RENDERER_TYPES
