"""Stable identity for an assessable task slot in written reports."""


def report_task_slot_key(
    *,
    source_selection_id: str = '',
    content_order: int = 0,
    position: int,
    occurrence: int = 1,
) -> str:
    """Identify the same specification slot across generated variants."""
    if source_selection_id:
        return f'selection:{source_selection_id}:slot:{occurrence}'
    if content_order:
        return f'content:{content_order}:slot:{occurrence}'
    return f'position:{position}'
