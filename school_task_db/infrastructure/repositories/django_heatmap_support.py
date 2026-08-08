"""Shared Django mappers for heatmap report adapters."""

from core_logic.entities.heatmap import ReportHeatmapColumnRef
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportGroupRef,
    ReportStudentRef,
    ReportWorkRef,
)
from curriculum.models import Course


def report_student_ref(student):
    return ReportStudentRef(
        pk=str(student.pk),
        full_name=student.get_full_name(),
        short_name=student.get_short_name(),
        last_name=student.last_name,
        first_name=student.first_name,
    )


def report_group_ref(group):
    return ReportGroupRef(
        pk=str(group.pk),
        name=group.name,
        students_count=group.students.count(),
    )


def report_course_ref(course):
    return ReportCourseRef(pk=str(course.pk), name=course.name)


def active_course_refs():
    return [
        report_course_ref(course)
        for course in Course.objects.filter(is_active=True).order_by(
            'grade_level',
            'name',
        )
    ]


def report_heatmap_column_ref(item):
    return ReportHeatmapColumnRef(
        pk=str(item.pk),
        name=item.name,
        section=getattr(item, 'section', ''),
    )


def report_work_ref(work):
    variant_count = getattr(work, 'variant_count', None)
    if variant_count is None:
        variant_count = work.variant_set.count()
    return ReportWorkRef(
        pk=str(work.pk),
        name=work.name,
        work_type=work.work_type,
        work_type_display=work.get_work_type_display(),
        duration=work.duration,
        variant_count=variant_count,
    )
