"""Resolve stable event metadata for historical performance reports."""

from core_logic.entities.event_performance_report import (
    EventReportCapturedEventFact,
    EventReportEventRef,
)
from core_logic.value_objects.work_assessment import (
    WORK_ASSESSMENT_MODE_VARIANT,
)


def resolve_event_report_assessment_mode(
    captured_modes,
    fallback_mode: str = WORK_ASSESSMENT_MODE_VARIANT,
) -> str:
    """Prefer one consistent historical mode, otherwise use the work mode."""
    return _consistent_value(
        captured_modes,
        fallback_mode or WORK_ASSESSMENT_MODE_VARIANT,
    )


def resolve_event_report_event_ref(
    current_event: EventReportEventRef,
    captured_events: tuple[EventReportCapturedEventFact, ...],
) -> EventReportEventRef:
    """Overlay consistent immutable facts onto current event metadata."""
    return EventReportEventRef(
        pk=current_event.pk,
        name=_consistent_value(
            (event.name for event in captured_events),
            current_event.name,
        ),
        status=current_event.status,
        status_display=current_event.status_display,
        planned_date=_consistent_value(
            (event.planned_date for event in captured_events),
            current_event.planned_date,
        ),
        work_name=_consistent_value(
            (event.work_name for event in captured_events),
            current_event.work_name,
        ),
        course_name=current_event.course_name,
        work_assessment_mode=resolve_event_report_assessment_mode(
            (
                event.work_assessment_mode
                for event in captured_events
            ),
            fallback_mode=current_event.work_assessment_mode,
        ),
    )


def _consistent_value(values, fallback):
    distinct_values = {
        value
        for value in values
        if value is not None and value != ''
    }
    if len(distinct_values) == 1:
        return distinct_values.pop()
    return fallback
