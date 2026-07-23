"""Document template repository interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.document import (
    CreateDocumentTemplateParams,
    CreatePrintSettingsParams,
    DocumentTemplateSpec,
    PrintSettingsSpec,
    UpdateDocumentTemplateParams,
    UpdatePrintSettingsParams,
)


class IDocumentTemplateRepository(ABC):
    def list_print_settings_specs(
        self,
        document_type: str = '',
    ) -> List[PrintSettingsSpec]:
        return self.list_template_specs(template_type=document_type)

    def get_default_print_settings_spec(
        self,
        document_type: str,
    ) -> Optional[PrintSettingsSpec]:
        return self.get_default_template_spec(template_type=document_type)

    def get_print_settings_spec(
        self,
        print_settings_id: str,
        document_type: str = '',
    ) -> Optional[PrintSettingsSpec]:
        return self.get_template_spec(
            template_id=print_settings_id,
            template_type=document_type,
        )

    def create_print_settings(
        self,
        params: CreatePrintSettingsParams,
    ) -> str:
        return self.create_template(params)

    def update_print_settings(
        self,
        params: UpdatePrintSettingsParams,
    ) -> bool:
        return self.update_template(params)

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
