"""Get variant delete screen data."""

from typing import Optional

from core_logic.entities.work import VariantDeleteInfo
from core_logic.interfaces.work_repo import IWorkRepository


class GetVariantDeleteInfoUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self, variant_id: str) -> Optional[VariantDeleteInfo]:
        return self.work_repo.get_variant_delete_info(variant_id)
