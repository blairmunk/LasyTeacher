"""Build codifier detail screen data."""

from core_logic.entities.codifier import CodifierDetailData
from core_logic.interfaces.codifier_repo import ICodifierRepository


class GetCodifierDetailUseCase:
    def __init__(self, codifier_repo: ICodifierRepository):
        self.codifier_repo = codifier_repo

    def execute(self, codifier_id: str) -> CodifierDetailData:
        codifier = self.codifier_repo.get_codifier(codifier_id)
        if codifier is None:
            return CodifierDetailData()

        return CodifierDetailData(
            codifier=codifier,
            content_tree=self.codifier_repo.get_content_tree(codifier_id),
            requirements=self.codifier_repo.get_requirements(codifier_id),
            coverage=self.codifier_repo.get_coverage(codifier_id),
        )
