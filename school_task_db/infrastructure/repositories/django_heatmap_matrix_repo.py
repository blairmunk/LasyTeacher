"""Django read adapter for heatmap matrices and timelines."""

from django.shortcuts import get_object_or_404

from core_logic.entities.heatmap import (
    HeatmapCourseTimelineSource,
    HeatmapMatrixSource,
    HeatmapScoreFact,
    HeatmapTimelineEventRef,
    HeatmapTimelineMarkFact,
    ReportHeatmapColumnRef,
)
from core_logic.interfaces.heatmap_matrix_repo import IHeatmapMatrixRepository
from curriculum.models import SubTopic, Topic
from events.models import Event, EventParticipation
from infrastructure.repositories.django_heatmap_support import (
    latest_attempt_task_results,
    report_student_ref,
)
from infrastructure.services.attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from students.models import Student


class DjangoHeatmapMatrixRepository(IHeatmapMatrixRepository):
    def get_heatmap_topic_matrix_source(self, student_ids, section_filter=''):
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        task_results = latest_attempt_task_results(student_ids)
        topic_sections = self._topic_sections(task_results)
        topic_orders = self._topic_orders(task_results)
        columns = {}
        scores = []
        for result in task_results:
            topic_id = result.task.topic_id
            section = (
                result.task.topic_section
                or topic_sections.get(topic_id, '')
            )
            if not topic_id or (section_filter and section != section_filter):
                continue
            columns.setdefault(
                topic_id,
                ReportHeatmapColumnRef(
                    pk=topic_id,
                    name=result.task.topic_name,
                    section=section,
                ),
            )
            scores.append(HeatmapScoreFact(
                student_id=result.student_id,
                column_id=topic_id,
                points=result.points,
                max_points=result.max_points,
            ))
        return HeatmapMatrixSource(
            students=[report_student_ref(student) for student in students],
            columns=sorted(
                columns.values(),
                key=lambda item: (
                    item.section,
                    topic_orders.get(item.pk, 0),
                    item.name,
                    item.pk,
                ),
            ),
            scores=scores,
        )

    def get_heatmap_course_topic_matrix_source(self, student_ids, work_ids):
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        task_results = latest_attempt_task_results(
            student_ids,
            work_ids=work_ids,
        )
        topic_sections = self._topic_sections(task_results)
        topic_orders = self._topic_orders(task_results)
        columns = {}
        scores = []
        for result in task_results:
            topic_id = result.task.topic_id
            if not topic_id:
                continue
            section = (
                result.task.topic_section
                or topic_sections.get(topic_id, '')
            )
            columns.setdefault(
                topic_id,
                ReportHeatmapColumnRef(
                    pk=topic_id,
                    name=result.task.topic_name,
                    section=section,
                ),
            )
            scores.append(HeatmapScoreFact(
                student_id=result.student_id,
                column_id=topic_id,
                points=result.points,
                max_points=result.max_points,
            ))
        return HeatmapMatrixSource(
            students=[report_student_ref(student) for student in students],
            columns=sorted(
                columns.values(),
                key=lambda item: (
                    item.section,
                    topic_orders.get(item.pk, 0),
                    item.name,
                    item.pk,
                ),
            ),
            scores=scores,
        )

    def get_heatmap_course_timeline_source(self, student_ids, work_ids):
        events = list(Event.objects.filter(
            work_id__in=work_ids,
            status='graded',
        ).order_by('planned_date'))
        participations = list(
            EventParticipation.objects.filter(
                event__in=events,
                student_id__in=student_ids,
            ).only('pk', 'event_id')
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in participations),
            include_task_results=False,
        )

        return HeatmapCourseTimelineSource(
            events=[
                HeatmapTimelineEventRef(
                    pk=str(event.pk),
                    name=event.name,
                    planned_date=event.planned_date,
                )
                for event in events
            ],
            marks=[
                HeatmapTimelineMarkFact(
                    event_id=str(participation.event_id),
                    points=attempt.points or 0,
                    max_points=attempt.max_points or 0,
                )
                for participation in participations
                if (attempt := attempts.get(participation.pk)) is not None
            ],
        )

    def get_heatmap_subtopic_matrix_source(self, student_ids, topic_id):
        topic = get_object_or_404(Topic, pk=topic_id)
        students = list(
            Student.objects.filter(pk__in=student_ids).order_by(
                'last_name',
                'first_name',
            ),
        )
        task_results = latest_attempt_task_results(student_ids)
        subtopic_orders = self._subtopic_orders(task_results)
        columns = {}
        scores = []
        for result in task_results:
            if result.task.topic_id != str(topic.pk):
                continue
            subtopic_id = result.task.subtopic_id
            if not subtopic_id:
                continue
            columns.setdefault(
                subtopic_id,
                ReportHeatmapColumnRef(
                    pk=subtopic_id,
                    name=result.task.subtopic_name,
                ),
            )
            scores.append(HeatmapScoreFact(
                student_id=result.student_id,
                column_id=subtopic_id,
                points=result.points,
                max_points=result.max_points,
            ))
        return HeatmapMatrixSource(
            students=[report_student_ref(student) for student in students],
            columns=sorted(
                columns.values(),
                key=lambda item: (
                    subtopic_orders.get(item.pk, 0),
                    item.name,
                    item.pk,
                ),
            ),
            scores=scores,
        )

    @staticmethod
    def _topic_sections(task_results):
        topic_ids = {
            result.task.topic_id
            for result in task_results
            if result.task.topic_id and not result.task.topic_section
        }
        return {
            str(topic.pk): topic.section
            for topic in Topic.objects.filter(pk__in=topic_ids)
        }

    @staticmethod
    def _topic_orders(task_results):
        topic_ids = {
            result.task.topic_id
            for result in task_results
            if result.task.topic_id
        }
        return {
            str(topic.pk): topic.order
            for topic in Topic.objects.filter(pk__in=topic_ids)
        }

    @staticmethod
    def _subtopic_orders(task_results):
        subtopic_ids = {
            result.task.subtopic_id
            for result in task_results
            if result.task.subtopic_id
        }
        return {
            str(subtopic.pk): subtopic.order
            for subtopic in SubTopic.objects.filter(pk__in=subtopic_ids)
        }
