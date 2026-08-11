"""Repository interface for persisting work variants."""

from abc import ABC, abstractmethod

from core_logic.interfaces.work_repo import (
    CreatedWorkVariantRef,
    CreatedWorkWithVariantsRef,
    CreateVariantParams,
    CreateWorkWithVariantFromTasksParams,
    CreateWorkWithVariantsParams,
)


class IWorkVariantCreationRepository(ABC):
    @abstractmethod
    def create_work_with_variants(
        self,
        params: CreateWorkWithVariantsParams,
    ) -> CreatedWorkWithVariantsRef:
        """Create a work and all supplied variants atomically."""

    @abstractmethod
    def create_variant_from_plan(self, params: CreateVariantParams) -> str:
        """Persist one immutable variant creation plan and return its ID."""

    @abstractmethod
    def create_work_with_variant_from_tasks(
        self,
        params: CreateWorkWithVariantFromTasksParams,
    ) -> CreatedWorkVariantRef:
        """Create a work and its first variant from selected tasks."""
