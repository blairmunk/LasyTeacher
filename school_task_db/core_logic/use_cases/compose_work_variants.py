"""Compose variants for a work."""

from dataclasses import dataclass

from core_logic.entities.work import ComposeWorkVariantsResult
from core_logic.interfaces.work_variant_generation_repo import (
    IWorkVariantGenerationRepository,
)


@dataclass(frozen=True)
class ComposeWorkVariantsRequest:
    work_id: str
    count: int


class ComposeWorkVariantsUseCase:
    def __init__(self, work_repo: IWorkVariantGenerationRepository):
        self.work_repo = work_repo

    def execute(
        self,
        request: ComposeWorkVariantsRequest,
    ) -> ComposeWorkVariantsResult:
        created_count = self.work_repo.compose_variants(
            work_id=request.work_id,
            count=request.count,
        )
        if created_count is None:
            return ComposeWorkVariantsResult(
                created_count=0,
                status='not_found',
            )

        return ComposeWorkVariantsResult(
            created_count=created_count,
        )
