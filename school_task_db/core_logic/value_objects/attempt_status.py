"""Status rules for immutable checked attempts."""


def resolve_historical_participation_status(
    current_status: str,
    has_attempt: bool,
) -> str:
    """A captured checked attempt remains graded despite later live edits."""
    return 'graded' if has_attempt else current_status
