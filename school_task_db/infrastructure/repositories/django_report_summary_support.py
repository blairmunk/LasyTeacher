"""Shared Django queries and mappers for summary report adapters."""

from django.db.models import Count, Q

from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportEventRef,
    ReportGroupRef,
    ReportStudentRef,
    ReportWorkRef,
)
from core_logic.services.event_service import EventService
from curriculum.models import Course
from events.models import Event, EventParticipation
from students.models import Student, StudentGroup


def event_scope(year):
    if year:
        date_range = (year.start_date, year.end_date)
        events = Event.objects.filter(planned_date__range=date_range)
        participations = EventParticipation.objects.filter(
            event__planned_date__range=date_range,
        )
        courses = Course.objects.filter(year_id=year.pk, is_active=True)
    else:
        events = Event.objects.all()
        participations = EventParticipation.objects.all()
        courses = Course.objects.filter(is_active=True)

    return events, participations, courses


def student_scope(year):
    if year:
        return (
            StudentGroup.objects.filter(academic_year_id=year.pk),
            Student.objects.filter(
                studentgroup__academic_year_id=year.pk,
            ).distinct(),
        )
    return StudentGroup.objects.all(), Student.objects.all()


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


def report_event_ref(event):
    progress_percentage = EventService.progress_percentage(
        event.participants_count_value,
        event.completed_count_value,
    )
    return ReportEventRef(
        pk=str(event.pk),
        name=event.name,
        status=event.status,
        status_display=event.get_status_display(),
        planned_date=event.planned_date,
        actual_end=event.actual_end,
        location=event.location,
        work=report_work_ref(event.work),
        participants_count=event.participants_count_value,
        graded_count=event.graded_count_value,
        progress_percentage=progress_percentage,
    )


def event_summary_queryset(queryset):
    return queryset.select_related('work').annotate(
        participants_count_value=Count(
            'eventparticipation',
            distinct=True,
        ),
        completed_count_value=Count(
            'eventparticipation',
            filter=Q(
                eventparticipation__status__in=('completed', 'graded'),
            ),
            distinct=True,
        ),
        graded_count_value=Count(
            'eventparticipation',
            filter=Q(eventparticipation__status='graded'),
            distinct=True,
        ),
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
