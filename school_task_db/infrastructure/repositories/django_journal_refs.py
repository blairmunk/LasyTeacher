"""Shared Django scopes and references for class journal adapters."""

from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportGroupRef,
    ReportStudentRef,
)
from curriculum.models import Course
from students.models import StudentGroup


def course_scope(year):
    if year:
        return Course.objects.filter(year_id=year.pk, is_active=True)
    return Course.objects.filter(is_active=True)


def group_scope(year):
    if year:
        return StudentGroup.objects.filter(academic_year_id=year.pk)
    return StudentGroup.objects.all()


def student_ref(student):
    return ReportStudentRef(
        pk=str(student.pk),
        full_name=student.get_full_name(),
        short_name=student.get_short_name(),
        last_name=student.last_name,
        first_name=student.first_name,
    )


def group_ref(group):
    return ReportGroupRef(
        pk=str(group.pk),
        name=group.name,
        students_count=group.students.count(),
    )


def course_ref(course):
    return ReportCourseRef(pk=str(course.pk), name=course.name)
