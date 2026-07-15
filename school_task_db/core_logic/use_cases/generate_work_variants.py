"""Generate variants for a work."""

from dataclasses import dataclass

from core_logic.entities.work import GenerateWorkVariantsResult
from core_logic.interfaces.work_repo import IWorkRepository


@dataclass(frozen=True)
class GenerateWorkVariantsRequest:
    work_id: str
    count: int


class GenerateWorkVariantsUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(
        self,
        request: GenerateWorkVariantsRequest,
    ) -> GenerateWorkVariantsResult:
        return GenerateWorkVariantsResult(
            created_count=self.work_repo.generate_variants(
                work_id=request.work_id,
                count=request.count,
            )
        )
