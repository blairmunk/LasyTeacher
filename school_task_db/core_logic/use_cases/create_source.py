"""Create a task source."""

from core_logic.entities.task import SourceCreateParams, SourceCreateResult
from core_logic.interfaces.source_repo import ISourceRepository


class CreateSourceUseCase:
    def __init__(self, source_repo: ISourceRepository):
        self.source_repo = source_repo

    def execute(self, params: SourceCreateParams) -> SourceCreateResult:
        return self.source_repo.create_source(params)
