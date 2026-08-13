"""Shared Django mappers for heatmap report adapters."""

from core_logic.entities.heatmap import ReportHeatmapColumnRef
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportGroupRef,
    ReportStudentRef,
    ReportTaskRef,
    ReportWorkRef,
)
from curriculum.models import Course
from events.models import EventParticipation
from infrastructure.services.django_captured_task_result_queries import (
    latest_assessable_task_results,
)


def latest_attempt_task_results(student_ids, work_ids=None):
    participations = EventParticipation.objects.filter(
        student_id__in=student_ids,
    ).only('pk')
    if work_ids is not None:
        participations = participations.filter(
            event__work_id__in=work_ids,
        )
    participation_ids = list(
        participations.values_list('pk', flat=True)
    )
    return latest_assessable_task_results(participation_ids)


def report_student_ref(student):
    return ReportStudentRef(
        pk=str(student.pk),
        full_name=student.get_full_name(),
        short_name=student.get_short_name(),
        last_name=student.last_name,
        first_name=student.first_name,
    )


def report_snapshot_task_ref(task):
    return ReportTaskRef(
        pk=task.task_id,
        text=task.text,
        difficulty=task.difficulty,
        difficulty_display=(
            task.difficulty_display or str(task.difficulty)
        ),
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
    return tuple(
        report_course_ref(course)
        for course in Course.objects.filter(is_active=True).order_by(
            'grade_level',
            'name',
        )
    )


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
