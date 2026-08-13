"""Django read adapter for heatmap overview pages."""

from django.shortcuts import get_object_or_404

from core_logic.entities.heatmap import (
    HeatmapCourseOverviewData,
    HeatmapDrilldownOverviewData,
    HeatmapOverviewData,
)
from core_logic.interfaces.heatmap_overview_repo import (
    IHeatmapOverviewRepository,
)
from curriculum.models import Course, CourseAssignment, Topic
from infrastructure.repositories.django_heatmap_support import (
    active_course_refs,
    report_course_ref,
    report_group_ref,
    report_heatmap_column_ref,
    report_student_ref,
    report_work_ref,
)
from students.models import Student, StudentGroup


class DjangoHeatmapOverviewRepository(IHeatmapOverviewRepository):
    def get_heatmap_drilldown_overview(self, topic_id, group_id):
        topic = get_object_or_404(Topic, pk=topic_id)
        groups = list(StudentGroup.objects.all().order_by('name'))
        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        else:
            selected_group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        return HeatmapDrilldownOverviewData(
            topic=report_heatmap_column_ref(topic),
            groups=tuple(report_group_ref(group) for group in groups),
            selected_group=(
                report_group_ref(selected_group)
                if selected_group
                else None
            ),
            students=tuple(report_student_ref(student) for student in students),
            courses=active_course_refs(),
        )

    def get_heatmap_course_overview(self, course_id, group_id):
        course = get_object_or_404(Course, pk=course_id)
        course_groups = list(course.student_groups.all().order_by('name'))

        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        elif course_groups:
            students = list(
                Student.objects.filter(
                    studentgroup__in=course_groups,
                ).distinct().order_by('last_name', 'first_name'),
            )
            selected_group = None
        else:
            students = list(Student.objects.all().order_by('last_name', 'first_name'))
            selected_group = None

        course_works = [
            assignment.work
            for assignment in CourseAssignment.objects.filter(
                course=course,
            ).select_related('work')
        ]

        return HeatmapCourseOverviewData(
            course=report_course_ref(course),
            groups=tuple(report_group_ref(group) for group in course_groups),
            selected_group=(
                report_group_ref(selected_group)
                if selected_group
                else None
            ),
            students=tuple(report_student_ref(student) for student in students),
            course_works=tuple(report_work_ref(work) for work in course_works),
            courses=active_course_refs(),
            active_course_pk=str(course.pk),
        )

    def get_heatmap_overview(self, group_id):
        groups = list(StudentGroup.objects.all().order_by('name'))
        if group_id:
            selected_group = get_object_or_404(StudentGroup, pk=group_id)
            students = list(
                selected_group.students.all().order_by('last_name', 'first_name'),
            )
        else:
            selected_group = None
            students = list(Student.objects.all().order_by('last_name', 'first_name'))

        sections = list(
            Topic.objects.filter(subject='Физика')
            .values_list('section', flat=True)
            .distinct()
            .order_by('section'),
        )

        return HeatmapOverviewData(
            groups=tuple(report_group_ref(group) for group in groups),
            selected_group=(
                report_group_ref(selected_group)
                if selected_group
                else None
            ),
            students=tuple(report_student_ref(student) for student in students),
            sections=tuple(sections),
            courses=active_course_refs(),
        )
