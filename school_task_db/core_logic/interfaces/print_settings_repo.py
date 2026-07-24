"""Repository interface for document print settings."""

from abc import ABC, abstractmethod
from typing import List, Optional

from core_logic.entities.document import (
    CreatePrintSettingsParams,
    PrintSettingsSpec,
    UpdatePrintSettingsParams,
)


class IPrintSettingsRepository(ABC):
    @abstractmethod
    def list_print_settings_specs(
        self,
        document_type: str = '',
    ) -> List[PrintSettingsSpec]:
        """Return print settings, optionally filtered by document type."""

    @abstractmethod
    def get_default_print_settings_spec(
        self,
        document_type: str,
    ) -> Optional[PrintSettingsSpec]:
        """Return the default print settings for a document type."""

    @abstractmethod
    def get_print_settings_spec(
        self,
        print_settings_id: str,
        document_type: str = '',
    ) -> Optional[PrintSettingsSpec]:
        """Return print settings by id, optionally constrained by type."""

    @abstractmethod
    def create_print_settings(
        self,
        params: CreatePrintSettingsParams,
    ) -> str:
        """Create print settings and return their id."""

    @abstractmethod
    def update_print_settings(
        self,
        params: UpdatePrintSettingsParams,
    ) -> bool:
        """Update print settings and return whether they existed."""
