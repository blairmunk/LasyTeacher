"""Django persistence for event performance reports."""

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
from core_logic.value_objects.task_scores import resolve_task_score_record
from codifier.models import ContentEntry
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
                    teacher_comment=mark.teacher_comment if mark else '',
                    needs_attention=mark.needs_attention if mark else False,
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
                        group_key=f'position:{variant_task.order}',
                        order=variant_task.order,
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
        ).select_related(
            'task',
            'task__topic',
            'task__subtopic',
        ).prefetch_related(
            'task__codifier_requirements__codifier',
        ):
            result[variant_task.variant_id].append(variant_task)
        return result

    @staticmethod
    def _specification_facts(variant_tasks):
        content_entries = (
            DjangoEventPerformanceReportRepository
            ._content_entries_by_code(variant_tasks)
        )
        facts = []
        seen = set()
        for tasks in variant_tasks.values():
            for variant_task in tasks:
                if not variant_task.is_assessable:
                    continue
                task = variant_task.task
                codifier_requirements = tuple(
                    f'{item.codifier.short_name}: {item.code}'
                    for item in task.codifier_requirements.all()
                )
                content_element_descriptions = (
                    DjangoEventPerformanceReportRepository
                    ._content_element_descriptions(
                        task,
                        content_entries.get(task.content_element.strip(), ()),
                    )
                )
                key = (
                    variant_task.order,
                    task.topic.name,
                    task.subtopic.name if task.subtopic_id else '',
                    task.content_element.strip(),
                    task.requirement_element.strip(),
                    codifier_requirements,
                    content_element_descriptions,
                )
                if key in seen:
                    continue
                seen.add(key)
                facts.append(
                    EventReportSpecificationFact(
                        order=key[0],
                        topic_name=key[1],
                        subtopic_name=key[2],
                        content_element=key[3],
                        requirement_element=key[4],
                        codifier_requirements=key[5],
                        content_element_descriptions=key[6],
                    )
                )
        return tuple(sorted(facts, key=lambda item: item.order))

    @staticmethod
    def _content_entries_by_code(variant_tasks):
        codes = {
            variant_task.task.content_element.strip()
            for tasks in variant_tasks.values()
            for variant_task in tasks
            if variant_task.is_assessable
            and variant_task.task.content_element.strip()
        }
        result = {code: [] for code in codes}
        if not codes:
            return result
        entries = ContentEntry.objects.filter(code__in=codes).select_related(
            'codifier',
            'topic',
            'subtopic',
        )
        for entry in entries:
            result[entry.code].append(entry)
        return result

    @staticmethod
    def _content_element_descriptions(task, candidates):
        if not candidates:
            return ()
        requirement_codifier_ids = {
            requirement.codifier_id
            for requirement in task.codifier_requirements.all()
        }
        selected = [
            entry
            for entry in candidates
            if entry.codifier_id in requirement_codifier_ids
        ]
        if not selected and task.subtopic_id:
            selected = [
                entry
                for entry in candidates
                if entry.subtopic_id == task.subtopic_id
            ]
        if not selected:
            selected = [
                entry
                for entry in candidates
                if entry.topic_id == task.topic_id
            ]
        if not selected and len(candidates) == 1:
            selected = list(candidates)
        return tuple(dict.fromkeys(
            f'{entry.codifier.short_name}: {entry.name}'
            for entry in selected
        ))

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
