"""Generate document files for a remedial sheet."""

from dataclasses import dataclass

from core_logic.entities.document_generation import DocumentGenerationResult
from core_logic.interfaces.document_generation import IDocumentGenerationService
from core_logic.value_objects.content_config import RemedialSheetGenerationOptions


@dataclass(frozen=True)
class GenerateRemedialSheetDocumentRequest:
    variant_id: str
    options: RemedialSheetGenerationOptions


class GenerateRemedialSheetDocumentUseCase:
    def __init__(self, document_generation_service: IDocumentGenerationService):
        self.document_generation_service = document_generation_service

    def execute(
        self,
        request: GenerateRemedialSheetDocumentRequest,
    ) -> DocumentGenerationResult:
        document = self.document_generation_service.generate_remedial_sheet(
            request.variant_id,
            request.options,
        )
        status = 'generated' if document.file_paths else 'empty'
        return DocumentGenerationResult(
            status=status,
            generator_type=request.options.generator_type,
            file_type=document.file_type,
            file_paths=document.file_paths,
        )
