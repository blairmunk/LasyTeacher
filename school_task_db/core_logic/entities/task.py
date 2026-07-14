"""Task-related domain entities."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TaskEntity:
    id: str
    text: str = ''
    difficulty: int = 1
    estimated_time: Optional[int] = None

