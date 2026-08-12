"""Import a curriculum catalog and attach codifier content to it."""

from core_logic.entities.curriculum_import import (
    CurriculumImportRequest,
    CurriculumImportResult,
)
from core_logic.interfaces.curriculum_import_repo import (
    ICurriculumImportRepository,
)
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.services.curriculum_import_validation import (
    validate_curriculum_import_definition,
)


class ImportCurriculumUseCase:
    def __init__(
        self,
        curriculum_repo: ICurriculumImportRepository,
        transaction_manager: ITransactionManager,
    ):
        self.curriculum_repo = curriculum_repo
        self.transaction_manager = transaction_manager

    def execute(self, request: CurriculumImportRequest) -> CurriculumImportResult:
        validate_curriculum_import_definition(request.definition)
        with self.transaction_manager.atomic():
            return self.curriculum_repo.apply_curriculum_import(
                request.definition,
                request.clear_existing,
            )
