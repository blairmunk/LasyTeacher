"""Get variant delete screen data."""

from typing import Optional

from core_logic.entities.work import VariantDeleteInfo
from core_logic.interfaces.variant_lifecycle_repo import (
    IVariantLifecycleRepository,
)


class GetVariantDeleteInfoUseCase:
    def __init__(self, variant_repo: IVariantLifecycleRepository):
        self.variant_repo = variant_repo

    def execute(self, variant_id: str) -> Optional[VariantDeleteInfo]:
        return self.variant_repo.get_variant_delete_info(variant_id)
