"""Document template repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.document import DocumentTemplateSpec


class IDocumentTemplateRepository(ABC):
    @abstractmethod
    def list_template_specs(
        self,
        template_type: str = '',
    ) -> List[DocumentTemplateSpec]:
        """Return document template specs, optionally filtered by type."""

    @abstractmethod
    def get_default_template_spec(
        self,
        template_type: str,
    ) -> Optional[DocumentTemplateSpec]:
        """Return the default template spec for a type, if one exists."""

    @abstractmethod
    def get_template_spec(
        self,
        template_id: str,
        template_type: str = '',
    ) -> Optional[DocumentTemplateSpec]:
        """Return a template spec by id, optionally constrained by type."""
