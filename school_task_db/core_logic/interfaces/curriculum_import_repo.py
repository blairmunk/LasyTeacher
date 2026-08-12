"""Persistence port for curriculum catalog imports."""

from abc import ABC, abstractmethod

from core_logic.entities.curriculum_import import (
    CurriculumImportDefinition,
    CurriculumImportResult,
)


class ICurriculumImportRepository(ABC):
    @abstractmethod
    def apply_curriculum_import(
        self,
        definition: CurriculumImportDefinition,
        clear_existing: bool,
    ) -> CurriculumImportResult:
        """Apply one validated catalog definition and its bindings."""
