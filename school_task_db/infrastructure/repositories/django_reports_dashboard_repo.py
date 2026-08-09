"""Django read adapter for the reports dashboard."""

from core_logic.entities.report_summary import (
    DashboardCourseGroupRef,
    DashboardGroupSource,
    DashboardMarkFact,
    DashboardParticipationFact,
    ReportsDashboardSource,
)
from core_logic.interfaces.reports_dashboard_repo import (
    IReportsDashboardRepository,
)
from infrastructure.repositories.django_report_summary_support import (
    event_scope,
    event_summary_queryset,
    report_course_ref,
    report_event_ref,
    report_group_ref,
    student_scope,
)
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from works.models import Work


class DjangoReportsDashboardRepository(IReportsDashboardRepository):
    def get_reports_dashboard_source(self, year):
        events, participations, courses = event_scope(year)
        groups, students = student_scope(year)
        event_rows = list(
            event_summary_queryset(events).order_by('-planned_date')
        )
        participation_rows = list(
            participations.only(
                'pk',
                'student_id',
                'event_id',
                'status',
            )
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in participation_rows),
            include_task_results=False,
        )
        return ReportsDashboardSource(
            total_students=students.count(),
            total_works=Work.objects.count(),
            events=[report_event_ref(event) for event in event_rows],
            participations=[
                DashboardParticipationFact(
                    student_id=str(participation.student_id),
                    event_id=str(participation.event_id),
                    status=participation.status,
                )
                for participation in participation_rows
            ],
            marks=[
                DashboardMarkFact(
                    student_id=str(participation.student_id),
                    event_id=str(participation.event_id),
                    score=attempt.score,
                    checked_at=attempt.checked_at_snapshot,
                )
                for participation in participation_rows
                if (attempt := attempts.get(participation.pk)) is not None
            ],
            groups=[
                self._group_source(group, year)
                for group in groups.order_by('name')
            ],
            courses=[
                report_course_ref(course)
                for course in courses.order_by('grade_level', 'name')
            ],
        )

    @staticmethod
    def _group_source(group, year):
        linked_courses = group.courses.all()
        if year:
            linked_courses = linked_courses.filter(year_id=year.pk)
        return DashboardGroupSource(
            group=report_group_ref(group),
            student_ids=[
                str(student_id)
                for student_id in group.students.values_list('pk', flat=True)
            ],
            course_links=[
                DashboardCourseGroupRef(
                    course_id=str(course.pk),
                    course_name=course.name,
                    group_id=str(group.pk),
                    group_name=group.name,
                )
                for course in linked_courses
            ],
        )
