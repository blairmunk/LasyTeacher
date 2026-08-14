"""Variant read repository interface."""

from abc import ABC, abstractmethod
from typing import Optional

from core_logic.entities.work import (
    VariantDetailTaskRow,
    VariantDetailVariant,
    VariantListItem,
)


class IVariantReadRepository(ABC):
    @abstractmethod
    def get_list_variants(self) -> tuple[VariantListItem, ...]:
        """Return variants for the variant list page."""

    @abstractmethod
    def get_variant_detail(
        self,
        variant_id: str,
    ) -> Optional[VariantDetailVariant]:
        """Return one variant detail read model, or None."""

    @abstractmethod
    def get_variant_detail_tasks(
        self,
        variant_id: str,
    ) -> tuple[VariantDetailTaskRow, ...]:
        """Return ordered task read models for the variant detail page."""

    @abstractmethod
    def get_variant_total_max_points(self, variant_id: str) -> int:
        """Return total max points for a variant."""
