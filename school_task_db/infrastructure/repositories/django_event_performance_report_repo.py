"""Django persistence for event performance reports."""

from collections import defaultdict

from core_logic.entities.event_performance_report import (
    EventPerformanceReportSource,
    EventReportEventRef,
    EventReportNarrative,
    EventReportParticipantFact,
    EventReportSpecificationFact,
    EventReportTaskScoreFact,
    SaveEventReportNarrativeParams,
    SaveEventReportNarrativeResult,
)
from core_logic.interfaces.event_performance_report_repo import (
    IEventPerformanceReportRepository,
)
from core_logic.value_objects.report_task_slot import report_task_slot_key
from events.models import Event, EventParticipation
from infrastructure.services.attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from infrastructure.services.task_content_snapshots import (
    task_content_snapshot_from_mapping,
)
from reports.models import EventReportNarrativeModel
from works.models import VariantTask


class DjangoEventPerformanceReportRepository(
    IEventPerformanceReportRepository,
):
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
        variant_tasks = self._variant_tasks_by_variant(participations)
        task_scores = []
        participant_facts = []
        for participation in participations:
            attempt = attempts.get(participation.pk)
            student_name = participation.student.get_full_name()
            participant_facts.append(
                EventReportParticipantFact(
                    student_id=str(participation.student_id),
                    student_name=student_name,
                    status=participation.status,
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
            slot_occurrences = defaultdict(int)
            for task_result in attempt.captured_task_results:
                if not task_result.is_assessable_snapshot:
                    continue
                occurrence_key = (
                    task_result.source_selection_id_snapshot,
                    task_result.content_order_snapshot,
                )
                slot_occurrences[occurrence_key] += 1
                task_snapshot = task_content_snapshot_from_mapping(
                    task_result.task_content_snapshot,
                )
                task_scores.append(
                    EventReportTaskScoreFact(
                        group_key=report_task_slot_key(
                            source_selection_id=(
                                task_result.source_selection_id_snapshot
                            ),
                            content_order=(
                                task_result.content_order_snapshot
                            ),
                            position=task_result.order_snapshot,
                            occurrence=slot_occurrences[occurrence_key],
                        ),
                        order=task_result.order_snapshot,
                        topic_name=task_snapshot.topic_name,
                        subtopic_name=task_snapshot.subtopic_name,
                        student_id=str(participation.student_id),
                        student_name=student_name,
                        points=self._number(task_result.points),
                        max_points=self._number(
                            task_result.checked_max_points
                            if task_result.checked_max_points is not None
                            else task_result.expected_max_points_snapshot
                        ),
                        comment=task_result.comment,
                    )
                )

        narrative_model = EventReportNarrativeModel.objects.filter(
            event=event,
        ).first()
        return EventPerformanceReportSource(
            event=EventReportEventRef(
                pk=str(event.pk),
                name=event.name,
                status=event.status,
                status_display=event.get_status_display(),
                planned_date=event.planned_date,
                work_name=event.work.name,
                course_name=event.course.name if event.course_id else '',
            ),
            participants=tuple(participant_facts),
            task_scores=tuple(task_scores),
            specification=self._specification_facts(variant_tasks),
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
    def _variant_tasks_by_variant(participations):
        variant_ids = {
            item.variant_id for item in participations if item.variant_id
        }
        result = {variant_id: [] for variant_id in variant_ids}
        for variant_task in VariantTask.objects.filter(
            variant_id__in=variant_ids,
        ):
            result[variant_task.variant_id].append(variant_task)
        return result

    @staticmethod
    def _specification_facts(variant_tasks):
        facts = []
        seen = set()
        for tasks in variant_tasks.values():
            slot_occurrences = defaultdict(int)
            for variant_task in sorted(
                tasks,
                key=lambda item: (item.order, str(item.pk)),
            ):
                if not variant_task.is_assessable:
                    continue
                occurrence_key = (
                    variant_task.source_selection_id,
                    variant_task.content_order,
                )
                slot_occurrences[occurrence_key] += 1
                group_key = report_task_slot_key(
                    source_selection_id=variant_task.source_selection_id,
                    content_order=variant_task.content_order,
                    position=variant_task.order,
                    occurrence=slot_occurrences[occurrence_key],
                )
                task = task_content_snapshot_from_mapping(
                    variant_task.task_snapshot,
                )
                codifier_requirements = tuple(
                    f'{item.codifier_short_name}: {item.code}'
                    for item in task.codifier_requirements
                )
                key = (
                    group_key,
                    variant_task.order,
                    task.topic_name,
                    task.subtopic_name,
                    task.content_element,
                    task.requirement_element,
                    codifier_requirements,
                    task.content_element_descriptions,
                )
                if key in seen:
                    continue
                seen.add(key)
                facts.append(
                    EventReportSpecificationFact(
                        group_key=key[0],
                        order=key[1],
                        topic_name=key[2],
                        subtopic_name=key[3],
                        content_element=key[4],
                        requirement_element=key[5],
                        codifier_requirements=key[6],
                        content_element_descriptions=key[7],
                    )
                )
        return tuple(sorted(facts, key=lambda item: item.order))

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
