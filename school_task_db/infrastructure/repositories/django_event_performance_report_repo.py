"""Django persistence for event performance reports."""

from core_logic.entities.event_performance_report import (
    EventReportCapturedEventFact,
    EventReportCapturedTaskFact,
    EventPerformanceReportSource,
    EventReportEventRef,
    EventReportNarrative,
    EventReportParticipantFact,
    SaveEventReportNarrativeParams,
    SaveEventReportNarrativeResult,
)
from core_logic.interfaces.event_performance_report_repo import (
    IEventPerformanceReportRepository,
)
from core_logic.services.event_report_task_fact_service import (
    EventReportTaskFactService,
)
from core_logic.services.event_report_source_service import (
    resolve_event_report_event_ref,
)
from core_logic.value_objects.attempt_status import (
    resolve_historical_participation_status,
)
from core_logic.value_objects.task_content_snapshot import (
    task_content_snapshot_from_mapping,
)
from events.models import Event, EventParticipation
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from reports.models import EventReportNarrativeModel


class DjangoEventPerformanceReportRepository(
    IEventPerformanceReportRepository,
):
    def __init__(self, task_fact_service=None):
        self.task_fact_service = (
            task_fact_service or EventReportTaskFactService()
        )

    def get_event_report_source(self, event_id: str):
        event = Event.objects.select_related('work', 'course').filter(
            pk=event_id,
        ).first()
        if event is None:
            return None

        participations = list(
            EventParticipation.objects.filter(event=event)
            .select_related('student', 'variant')
            .order_by('student__last_name', 'student__first_name')
        )
        attempts = latest_attempts_by_participation(
            participation.pk for participation in participations
        )
        captured_tasks = []
        participant_facts = []
        for participation in participations:
            attempt = attempts.get(participation.pk)
            student_id = (
                attempt.student_id_snapshot
                if attempt
                else str(participation.student_id)
            )
            student_name = (
                attempt.student_name_snapshot
                if attempt
                else participation.student.get_full_name()
            )
            participant_facts.append(
                EventReportParticipantFact(
                    student_id=student_id,
                    student_name=student_name,
                    status=resolve_historical_participation_status(
                        participation.status,
                        has_attempt=attempt is not None,
                    ),
                    score=attempt.score if attempt else None,
                    points=self._number(attempt.points) if attempt else None,
                    max_points=(
                        self._number(attempt.max_points) if attempt else None
                    ),
                    mistakes_analysis=(
                        attempt.mistakes_analysis if attempt else ''
                    ),
                    recommendations=attempt.recommendations if attempt else '',
                    teacher_comment=attempt.teacher_comment if attempt else '',
                    needs_attention=(
                        attempt.needs_attention if attempt else False
                    ),
                )
            )
            if attempt is None:
                continue
            for task_result in attempt.captured_task_results:
                try:
                    task_snapshot = task_content_snapshot_from_mapping(
                        task_result.task_content_snapshot,
                    )
                except (TypeError, ValueError):
                    continue
                captured_tasks.append(
                    EventReportCapturedTaskFact(
                        order=task_result.order_snapshot,
                        topic_name=task_snapshot.topic_name,
                        subtopic_name=task_snapshot.subtopic_name,
                        student_id=student_id,
                        student_name=student_name,
                        points=self._number(task_result.points),
                        max_points=self._number(
                            task_result.checked_max_points
                            if task_result.checked_max_points is not None
                            else task_result.expected_max_points_snapshot
                        ),
                        comment=task_result.comment,
                        source_selection_id=(
                            task_result.source_selection_id_snapshot
                        ),
                        content_order=task_result.content_order_snapshot,
                        is_assessable=(
                            task_result.is_assessable_snapshot
                        ),
                        content_element=task_snapshot.content_element,
                        requirement_element=task_snapshot.requirement_element,
                        codifier_requirements=tuple(
                            f'{item.codifier_short_name}: {item.code}'
                            for item in task_snapshot.codifier_requirements
                        ),
                        content_element_descriptions=(
                            task_snapshot.content_element_descriptions
                        ),
                    )
                )

        task_facts = self.task_fact_service.build(captured_tasks)
        narrative_model = EventReportNarrativeModel.objects.filter(
            event=event,
        ).first()
        current_event_ref = EventReportEventRef(
            pk=str(event.pk),
            name=event.name,
            status=event.status,
            status_display=event.get_status_display(),
            planned_date=event.planned_date,
            work_name=event.work.name,
            course_name=event.course.name if event.course_id else '',
            work_assessment_mode=event.work.assessment_mode,
        )
        captured_event_facts = tuple(
            EventReportCapturedEventFact(
                name=attempt.event_name_snapshot,
                planned_date=attempt.event_date_snapshot,
                work_name=attempt.work_name_snapshot,
                work_assessment_mode=(
                    attempt.work_assessment_mode_snapshot
                ),
            )
            for attempt in attempts.values()
        )
        return EventPerformanceReportSource(
            event=resolve_event_report_event_ref(
                current_event_ref,
                captured_event_facts,
            ),
            participants=tuple(participant_facts),
            task_scores=task_facts.task_scores,
            specification=task_facts.specification,
            narrative=self._narrative(narrative_model),
        )

    def save_event_report_narrative(self, params):
        if not Event.objects.filter(pk=params.event_id).exists():
            return SaveEventReportNarrativeResult(status='not_found')
        narrative = params.narrative
        EventReportNarrativeModel.objects.update_or_create(
            event_id=params.event_id,
            defaults={
                'possible_causes': narrative.possible_causes,
                'recommendations': narrative.recommendations,
                'planned_actions': narrative.planned_actions,
                'additional_notes': narrative.additional_notes,
            },
        )
        return SaveEventReportNarrativeResult(
            status='saved',
            event_id=params.event_id,
        )

    @staticmethod
    def _narrative(model):
        if model is None:
            return EventReportNarrative()
        return EventReportNarrative(
            possible_causes=model.possible_causes,
            recommendations=model.recommendations,
            planned_actions=model.planned_actions,
            additional_notes=model.additional_notes,
        )

    @staticmethod
    def _number(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
