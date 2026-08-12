"""Seed editable fallback reference catalogs."""

from core_logic.entities.reference_seed import (
    SeedReferencesRequest,
    SeedReferencesResult,
)
from core_logic.interfaces.reference_seed_repo import IReferenceSeedRepository
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.services.reference_seed_validation import (
    validate_reference_seed_definition,
)


class SeedReferencesUseCase:
    def __init__(
        self,
        reference_repo: IReferenceSeedRepository,
        transaction_manager: ITransactionManager,
    ):
        self.reference_repo = reference_repo
        self.transaction_manager = transaction_manager

    def execute(self, request: SeedReferencesRequest) -> SeedReferencesResult:
        validate_reference_seed_definition(request.definition)
        with self.transaction_manager.atomic():
            mutations = [
                self.reference_repo.seed_simple_reference(
                    item,
                    request.replace_existing,
                )
                for item in request.definition.simple_references
            ]
            mutations.extend(
                self.reference_repo.seed_subject_reference(
                    item,
                    request.replace_existing,
                )
                for item in request.definition.subject_references
            )
        return SeedReferencesResult(mutations=tuple(mutations))
