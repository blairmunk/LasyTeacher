"""Build codifier list screen data."""

from core_logic.entities.codifier import CodifierListData
from core_logic.interfaces.codifier_catalog_repo import (
    ICodifierCatalogRepository,
)


class GetCodifierListUseCase:
    def __init__(self, codifier_repo: ICodifierCatalogRepository):
        self.codifier_repo = codifier_repo

    def execute(self) -> CodifierListData:
        return CodifierListData(
            codifiers=self.codifier_repo.get_list_codifiers(),
        )
