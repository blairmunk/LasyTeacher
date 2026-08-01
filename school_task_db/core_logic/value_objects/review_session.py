"""Values derived from review session state."""

from datetime import datetime
from typing import Optional


def review_session_progress_percentage(
    total_participations: int,
    checked_participations: int,
) -> float:
    if total_participations <= 0:
        return 0
    return round(
        checked_participations / total_participations * 100,
        1,
    )


def review_session_is_completed(finished_at: Optional[datetime]) -> bool:
    return finished_at is not None
