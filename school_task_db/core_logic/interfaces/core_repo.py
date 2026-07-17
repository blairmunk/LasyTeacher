"""Core repository interface."""

from abc import ABC, abstractmethod


class ICoreRepository(ABC):
    @abstractmethod
    def count_tasks(self) -> int:
        """Return task count."""

    @abstractmethod
    def count_works(self) -> int:
        """Return work count."""

    @abstractmethod
    def count_variants(self) -> int:
        """Return variant count."""

    @abstractmethod
    def count_orphan_variants(self) -> int:
        """Return variants not attached to a work."""

    @abstractmethod
    def count_students(self) -> int:
        """Return student count."""

    @abstractmethod
    def count_events(self) -> int:
        """Return event count."""

    @abstractmethod
    def count_analog_groups(self) -> int:
        """Return analog group count."""
