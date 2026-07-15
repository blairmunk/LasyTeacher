"""Generate document files for a work."""

from dataclasses import dataclass
from typing import Any

from core_logic.entities.document_generation import DocumentGenerationResult
from core_logic.interfaces.document_generation import IDocumentGenerationService
from core_logic.value_objects.content_config import WorkGenerationOptions


SUPPORTED_WORK_GENERATOR_TYPES = {'latex', 'html', 'pdf'}


@dataclass(frozen=True)
class GenerateWorkDocumentRequest:
    work: Any
    options: WorkGenerationOptions


class GenerateWorkDocumentUseCase:
    def __init__(self, document_generation_service: IDocumentGenerationService):
        self.document_generation_service = document_generation_service

    def execute(
        self,
        request: GenerateWorkDocumentRequest,
    ) -> DocumentGenerationResult:
        generator_type = request.options.generator_type
        if generator_type not in SUPPORTED_WORK_GENERATOR_TYPES:
            return DocumentGenerationResult(
                status='unsupported_generator',
                generator_type=generator_type,
            )

        document = self.document_generation_service.generate_work(
            request.work,
            request.options,
        )
        return DocumentGenerationResult(
            status='generated',
            generator_type=generator_type,
            file_type=document.file_type,
            file_paths=document.file_paths,
        )
