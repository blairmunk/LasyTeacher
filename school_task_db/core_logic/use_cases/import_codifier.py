"""Import one built-in codifier definition."""

from core_logic.entities.codifier_import import (
    ImportCodifierRequest,
    ImportCodifierResult,
)
from core_logic.interfaces.codifier_import_repo import (
    ICodifierImportRepository,
)
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.services.codifier_import_validation import (
    validate_codifier_import_definition,
)


class ImportCodifierUseCase:
    def __init__(
        self,
        codifier_repo: ICodifierImportRepository,
        transaction_manager: ITransactionManager,
    ):
        self.codifier_repo = codifier_repo
        self.transaction_manager = transaction_manager

    def execute(self, request: ImportCodifierRequest) -> ImportCodifierResult:
        definition = request.definition
        validate_codifier_import_definition(definition)
        with self.transaction_manager.atomic():
            deleted_count = 0
            if request.clear_existing:
                deleted_count = self.codifier_repo.delete_codifier(
                    definition.exam_type,
                    definition.year,
                    definition.subject,
                )
            elif self.codifier_repo.codifier_exists(
                definition.exam_type,
                definition.year,
                definition.subject,
            ):
                return ImportCodifierResult(status='already_exists')

            display_name = self.codifier_repo.create_codifier(definition)
        return ImportCodifierResult(
            status='imported',
            display_name=display_name,
            deleted_count=deleted_count,
            content_count=len(definition.content),
            requirements_count=len(definition.requirements),
        )
