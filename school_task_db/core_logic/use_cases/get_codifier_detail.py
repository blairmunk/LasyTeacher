"""Build codifier detail screen data."""

from core_logic.entities.codifier import CodifierDetailData
from core_logic.interfaces.codifier_repo import ICodifierRepository


class GetCodifierDetailUseCase:
    def __init__(self, codifier_repo: ICodifierRepository):
        self.codifier_repo = codifier_repo

    def get_queryset(self):
        return self.codifier_repo.get_detail_codifiers()

    def execute(self, codifier_id: str) -> CodifierDetailData:
        return CodifierDetailData(
            content_tree=self.codifier_repo.get_content_tree(codifier_id),
            requirements=self.codifier_repo.get_requirements(codifier_id),
            coverage=self.codifier_repo.get_coverage(codifier_id),
        )
