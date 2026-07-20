"""Document template repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    DocumentTemplateSpec,
    UpdateDocumentTemplateParams,
)


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

    @abstractmethod
    def create_template(
        self,
        params: CreateDocumentTemplateParams,
    ) -> str:
        """Create a document template and return its id."""

    @abstractmethod
    def update_template(
        self,
        params: UpdateDocumentTemplateParams,
    ) -> bool:
        """Update a document template and return whether it existed."""
