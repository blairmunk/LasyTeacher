"""Codifier repository interface."""

from abc import ABC, abstractmethod
from typing import Any


class ICodifierRepository(ABC):
    @abstractmethod
    def get_list_codifiers(self) -> Any:
        """Return codifiers for the codifier list page."""

    @abstractmethod
    def get_detail_codifiers(self) -> Any:
        """Return codifiers for the codifier detail page lookup."""

    @abstractmethod
    def get_content_tree(self, codifier_id: str) -> Any:
        """Return root content entries for one codifier."""

    @abstractmethod
    def get_requirements(self, codifier_id: str) -> Any:
        """Return requirements for one codifier."""

    @abstractmethod
    def get_coverage(self, codifier_id: str) -> dict:
        """Return content coverage for one codifier."""
