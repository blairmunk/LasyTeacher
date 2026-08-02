"""References returned after capturing a checked student attempt."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AttemptSnapshotRef:
    pk: str
    participation_id: str
    mark_id: str
    revision: int

