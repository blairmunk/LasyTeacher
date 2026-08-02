"""Port for immutable revisions of checked student attempts."""

from abc import ABC, abstractmethod

from core_logic.entities.attempt_snapshot import AttemptSnapshotRef


class IAttemptSnapshotRepository(ABC):
    @abstractmethod
    def capture_mark(self, mark_id: str) -> AttemptSnapshotRef:
        """Capture the current checked mark as a new immutable revision."""

