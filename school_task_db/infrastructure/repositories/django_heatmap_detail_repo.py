"""Django read adapter for detailed heatmap reports."""

from django.shortcuts import get_object_or_404

from core_logic.entities.heatmap import (
    HeatmapDetailScoreFact,
    HeatmapStudentDetailSource,
    HeatmapSubtopicDetailSource,
    ReportHeatmapColumnRef,
)
from core_logic.entities.report_refs import (
    ReportActivityRef,
    ReportCourseRef,
    ReportGroupRef,
)
from core_logic.interfaces.heatmap_detail_repo import IHeatmapDetailRepository
from curriculum.models import Course, SubTopic, Topic
from infrastructure.repositories.django_heatmap_support import (
    latest_attempt_task_results,
    report_snapshot_task_ref,
    report_student_ref,
)
from students.models import Student, StudentGroup


class DjangoHeatmapDetailRepository(IHeatmapDetailRepository):
    def get_heatmap_subtopic_detail_source(self, subtopic_id, group_id):
        subtopic = get_object_or_404(SubTopic, pk=subtopic_id)
        topic = subtopic.topic
        group_models = list(StudentGroup.objects.all().order_by('name'))
        if group_id:
            selected_group_model = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group_model.students.all().order_by(
                    'last_name',
                    'first_name',
                ),
            )
        else:
            selected_group_model = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        task_results = [
            result
            for result in latest_attempt_task_results(
                [student.pk for student in students],
            )
            if result.task.subtopic_id == str(subtopic.pk)
        ]
        task_refs = {}
        for result in task_results:
            task_refs.setdefault(
                result.task.task_id,
                report_snapshot_task_ref(result.task),
            )

        return HeatmapSubtopicDetailSource(
            subtopic=ReportHeatmapColumnRef(
                pk=str(subtopic.pk),
                name=subtopic.name,
            ),
            topic=ReportHeatmapColumnRef(
                pk=str(topic.pk),
                name=topic.name,
                section=topic.section,
            ),
            groups=tuple(
                ReportGroupRef(
                    pk=str(group.pk),
                    name=group.name,
                    students_count=group.students.count(),
                )
                for group in group_models
            ),
            selected_group=(
                ReportGroupRef(
                    pk=str(selected_group_model.pk),
                    name=selected_group_model.name,
                    students_count=selected_group_model.students.count(),
                )
                if selected_group_model
                else None
            ),
            students=tuple(
                report_student_ref(student)
                for student in students
            ),
            tasks=tuple(sorted(
                task_refs.values(),
                key=lambda task: (task.difficulty, task.text, task.pk),
            )),
            scores=tuple(
                HeatmapDetailScoreFact(
                    student_id=result.student_id,
                    task_id=result.task.task_id,
                    subtopic_id=result.task.subtopic_id,
                    points=result.points,
                    max_points=result.max_points,
                    event=ReportActivityRef(
                        pk=result.event_id,
                        name=result.event_name,
                        planned_date=result.event_date,
                    ),
                )
                for result in task_results
            ),
            courses=tuple(
                ReportCourseRef(
                    pk=str(course.pk),
                    name=course.name,
                )
                for course in Course.objects.filter(is_active=True).order_by(
                    'grade_level',
                    'name',
                )
            ),
        )

    def get_heatmap_student_detail_source(
        self,
        topic_id,
        student_id,
        subtopic_id=None,
    ):
        topic = get_object_or_404(Topic, pk=topic_id)
        student = get_object_or_404(Student, pk=student_id)
        selected_subtopic_model = None
        if subtopic_id:
            selected_subtopic_model = SubTopic.objects.filter(
                pk=subtopic_id,
                topic=topic,
            ).first()

        task_results = [
            result
            for result in latest_attempt_task_results([student.pk])
            if result.task.topic_id == str(topic.pk)
        ]
        task_refs = {}
        for result in task_results:
            task_refs.setdefault(
                result.task.task_id,
                report_snapshot_task_ref(result.task),
            )
        subtopic_models = list(
            SubTopic.objects.filter(topic=topic).order_by('order', 'name'),
        )

        return HeatmapStudentDetailSource(
            topic=ReportHeatmapColumnRef(
                pk=str(topic.pk),
                name=topic.name,
                section=topic.section,
            ),
            student=report_student_ref(student),
            selected_subtopic=(
                ReportHeatmapColumnRef(
                    pk=str(selected_subtopic_model.pk),
                    name=selected_subtopic_model.name,
                )
                if selected_subtopic_model
                else None
            ),
            subtopics=tuple(
                ReportHeatmapColumnRef(
                    pk=str(subtopic.pk),
                    name=subtopic.name,
                )
                for subtopic in subtopic_models
            ),
            tasks=tuple(sorted(
                task_refs.values(),
                key=lambda task: (task.difficulty, task.text, task.pk),
            )),
            scores=tuple(
                HeatmapDetailScoreFact(
                    student_id=result.student_id,
                    task_id=result.task.task_id,
                    subtopic_id=result.task.subtopic_id,
                    points=result.points,
                    max_points=result.max_points,
                    event=ReportActivityRef(
                        pk=result.event_id,
                        name=result.event_name,
                        planned_date=result.event_date,
                    ),
                )
                for result in task_results
            ),
            courses=tuple(
                ReportCourseRef(
                    pk=str(course.pk),
                    name=course.name,
                )
                for course in Course.objects.filter(is_active=True).order_by(
                    'grade_level',
                    'name',
                )
            ),
        )
