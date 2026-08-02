"""Django persistence for event performance reports."""

from core_logic.entities.event_performance_report import (
    EventPerformanceReportSource,
    EventReportEventRef,
    EventReportNarrative,
    EventReportParticipantFact,
    EventReportTaskScoreFact,
    SaveEventReportNarrativeParams,
    SaveEventReportNarrativeResult,
)
from core_logic.interfaces.event_performance_report_repo import (
    IEventPerformanceReportRepository,
)
from core_logic.value_objects.task_scores import resolve_task_score_record
from events.models import Event, EventParticipation, Mark
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
        marks = {
            mark.participation_id: mark
            for mark in Mark.objects.filter(
                participation_id__in=[item.pk for item in participations],
            )
        }
        variant_tasks = self._variant_tasks_by_variant(participations)
        task_scores = []
        participant_facts = []
        for participation in participations:
            mark = marks.get(participation.pk)
            student_name = participation.student.get_full_name()
            participant_facts.append(
                EventReportParticipantFact(
                    student_id=str(participation.student_id),
                    student_name=student_name,
                    status=participation.status,
                    score=mark.score if mark else None,
                    points=self._number(mark.points) if mark else None,
                    max_points=self._number(mark.max_points) if mark else None,
                    mistakes_analysis=mark.mistakes_analysis if mark else '',
                    recommendations=mark.recommendations if mark else '',
                )
            )
            if mark is None or participation.variant_id is None:
                continue
            for variant_task in variant_tasks.get(participation.variant_id, []):
                if not variant_task.is_assessable:
                    continue
                record = resolve_task_score_record(
                    mark.task_scores,
                    variant_task_id=str(variant_task.pk),
                    task_id=str(variant_task.task_id),
                )
                if record is None:
                    continue
                task_scores.append(
                    EventReportTaskScoreFact(
                        group_key=(
                            variant_task.source_selection_id
                            or f'order:{variant_task.content_order or variant_task.order}'
                        ),
                        order=variant_task.content_order or variant_task.order,
                        task_id=str(variant_task.task_id),
                        task_text=variant_task.task.text,
                        topic_name=variant_task.task.topic.name,
                        subtopic_name=(
                            variant_task.task.subtopic.name
                            if variant_task.task.subtopic_id
                            else ''
                        ),
                        student_id=str(participation.student_id),
                        student_name=student_name,
                        points=self._number(record.points),
                        max_points=self._number(record.max_points),
                        comment=record.comment,
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
        ).select_related('task', 'task__topic', 'task__subtopic'):
            result[variant_task.variant_id].append(variant_task)
        return result

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
