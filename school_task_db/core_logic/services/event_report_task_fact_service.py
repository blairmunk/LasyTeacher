"""Build stable report task slots from captured attempt facts."""

from collections import defaultdict

from core_logic.entities.event_performance_report import (
    EventReportSpecificationFact,
    EventReportTaskFacts,
    EventReportTaskScoreFact,
)
from core_logic.value_objects.report_task_slot import report_task_slot_key


class EventReportTaskFactService:
    @staticmethod
    def build(captured_tasks) -> EventReportTaskFacts:
        slot_occurrences = defaultdict(int)
        task_scores = []
        specification = []
        seen_specification = set()
        for task in captured_tasks:
            if not task.is_assessable:
                continue
            occurrence_key = (
                task.student_id,
                task.source_selection_id,
                task.content_order,
            )
            slot_occurrences[occurrence_key] += 1
            group_key = report_task_slot_key(
                source_selection_id=task.source_selection_id,
                content_order=task.content_order,
                position=task.order,
                occurrence=slot_occurrences[occurrence_key],
            )
            task_scores.append(
                EventReportTaskScoreFact(
                    group_key=group_key,
                    order=task.order,
                    topic_name=task.topic_name,
                    subtopic_name=task.subtopic_name,
                    student_id=task.student_id,
                    student_name=task.student_name,
                    points=task.points,
                    max_points=task.max_points,
                    comment=task.comment,
                )
            )
            specification_key = (
                group_key,
                task.order,
                task.topic_name,
                task.subtopic_name,
                task.content_element,
                task.requirement_element,
                task.codifier_requirements,
                task.content_element_descriptions,
            )
            if specification_key in seen_specification:
                continue
            seen_specification.add(specification_key)
            specification.append(
                EventReportSpecificationFact(
                    group_key=group_key,
                    order=task.order,
                    topic_name=task.topic_name,
                    subtopic_name=task.subtopic_name,
                    content_element=task.content_element,
                    requirement_element=task.requirement_element,
                    codifier_requirements=task.codifier_requirements,
                    content_element_descriptions=(
                        task.content_element_descriptions
                    ),
                )
            )
        return EventReportTaskFacts(
            task_scores=tuple(task_scores),
            specification=tuple(sorted(
                specification,
                key=lambda item: (
                    item.order,
                    item.group_key,
                    item.topic_name,
                ),
            )),
        )
