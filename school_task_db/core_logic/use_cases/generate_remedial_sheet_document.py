"""Generate document files for a remedial sheet."""

from dataclasses import dataclass

from core_logic.entities.document_generation import DocumentGenerationResult
from core_logic.interfaces.document_generation import IDocumentGenerationService
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.value_objects.content_config import RemedialSheetGenerationOptions


SUPPORTED_REMEDIAL_SHEET_GENERATOR_TYPES = {'latex', 'html', 'pdf'}


@dataclass(frozen=True)
class GenerateRemedialSheetDocumentRequest:
    variant_id: str
    options: RemedialSheetGenerationOptions


class GenerateRemedialSheetDocumentUseCase:
    def __init__(
        self,
        document_generation_service: IDocumentGenerationService,
        work_repo: IWorkRepository,
    ):
        self.document_generation_service = document_generation_service
        self.work_repo = work_repo

    def execute(
        self,
        request: GenerateRemedialSheetDocumentRequest,
    ) -> DocumentGenerationResult:
        variant_type = self.work_repo.get_variant_type(request.variant_id)
        if variant_type is None:
            return DocumentGenerationResult(
                status='not_found',
                generator_type=request.options.generator_type,
            )
        if variant_type != 'remedial':
            return DocumentGenerationResult(
                status='not_remedial',
                generator_type=request.options.generator_type,
            )
        if (
            request.options.generator_type
            not in SUPPORTED_REMEDIAL_SHEET_GENERATOR_TYPES
        ):
            return DocumentGenerationResult(
                status='unsupported_generator',
                generator_type=request.options.generator_type,
            )

        document = self.document_generation_service.generate_remedial_sheet(
            request.variant_id,
            request.options,
        )
        status = 'generated' if document.files else 'empty'
        return DocumentGenerationResult(
            status=status,
            generator_type=request.options.generator_type,
            file_type=document.file_type,
            files=document.files,
        )
