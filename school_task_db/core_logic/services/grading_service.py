"""Pure grading decisions."""


class GradingService:
    """Business rules for grading workflow state."""

    def checked_by_name(self, display_name: str = '', username: str = '') -> str:
        return display_name or username or 'Учитель'

    def next_event_status(
        self,
        current_status: str,
        active_participants: int,
        graded_participants: int,
    ) -> str:
        if active_participants > 0 and active_participants == graded_participants:
            return 'graded'
        if current_status not in ('reviewing', 'graded'):
            return 'reviewing'
        return current_status
