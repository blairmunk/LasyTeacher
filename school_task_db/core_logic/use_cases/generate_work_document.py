"""Generate document files for a work."""

from dataclasses import dataclass

from core_logic.entities.document_generation import DocumentGenerationResult
from core_logic.interfaces.document_generation import IDocumentGenerationService
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.value_objects.content_config import WorkGenerationOptions


SUPPORTED_WORK_GENERATOR_TYPES = {'latex', 'html', 'pdf'}


@dataclass(frozen=True)
class GenerateWorkDocumentRequest:
    work_id: str
    options: WorkGenerationOptions


class GenerateWorkDocumentUseCase:
    def __init__(
        self,
        document_generation_service: IDocumentGenerationService,
        work_repo: IWorkRepository,
    ):
        self.document_generation_service = document_generation_service
        self.work_repo = work_repo

    def execute(
        self,
        request: GenerateWorkDocumentRequest,
    ) -> DocumentGenerationResult:
        generator_type = request.options.generator_type
        work_name = self.work_repo.get_work_name(request.work_id)
        if work_name is None:
            return DocumentGenerationResult(
                status='not_found',
                generator_type=generator_type,
            )

        if generator_type not in SUPPORTED_WORK_GENERATOR_TYPES:
            return DocumentGenerationResult(
                status='unsupported_generator',
                generator_type=generator_type,
                source_name=work_name,
            )

        document = self.document_generation_service.generate_work(
            request.work_id,
            request.options,
        )
        return DocumentGenerationResult(
            status='generated',
            generator_type=generator_type,
            file_type=document.file_type,
            files=document.files,
            source_name=work_name,
        )
