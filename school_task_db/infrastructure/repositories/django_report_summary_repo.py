"""Django repository for dashboard and summary reports."""

from collections import defaultdict

from django.db.models import Count, Q

from core_logic.entities.report_summary import (
    DashboardCourseGroupRef,
    DashboardGroupSource,
    DashboardMarkFact,
    DashboardParticipationFact,
    EventsStatusSource,
    ReportsDashboardSource,
    StudentPerformanceItemSource,
    StudentPerformanceParticipationFact,
    StudentPerformanceSource,
    WorkAnalysisItemSource,
    WorkAnalysisSource,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportEventRef,
    ReportGroupRef,
    ReportMarkFact,
    ReportStudentRef,
    ReportWorkRef,
)
from core_logic.interfaces.events_status_repo import IEventsStatusRepository
from core_logic.interfaces.reports_dashboard_repo import (
    IReportsDashboardRepository,
)
from core_logic.interfaces.student_performance_repo import (
    IStudentPerformanceRepository,
)
from core_logic.interfaces.work_analysis_repo import IWorkAnalysisRepository
from core_logic.services.event_service import EventService
from curriculum.models import Course
from events.models import Event, EventParticipation
from infrastructure.services.attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from students.models import Student, StudentGroup
from works.models import Work


class DjangoReportSummaryRepository(
    IEventsStatusRepository,
    IReportsDashboardRepository,
    IStudentPerformanceRepository,
    IWorkAnalysisRepository,
):
    def get_reports_dashboard_source(self, year):
        events, participations, courses = self._get_event_scope(year)
        groups, students = self._get_student_scope(year)
        event_rows = list(
            self._event_summary_queryset(events).order_by('-planned_date')
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
        course_rows = list(courses.order_by('grade_level', 'name'))
        return ReportsDashboardSource(
            total_students=students.count(),
            total_works=Work.objects.count(),
            events=[
                self._report_event_ref(event)
                for event in event_rows
            ],
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
                self._dashboard_group_source(group, year)
                for group in groups.order_by('name')
            ],
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in course_rows
            ],
        )

    def _dashboard_group_source(self, group, year):
        linked_courses = group.courses.all()
        if year:
            linked_courses = linked_courses.filter(year_id=year.pk)
        return DashboardGroupSource(
            group=ReportGroupRef(
                pk=str(group.pk),
                name=group.name,
                students_count=group.students.count(),
            ),
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

    def get_events_status_source(self, year):
        events, participations, courses = self._get_event_scope(year)
        return EventsStatusSource(
            events=[
                self._report_event_ref(event)
                for event in self._event_summary_queryset(events).order_by(
                    '-planned_date',
                )
            ],
            participation_statuses=list(
                participations.values_list('status', flat=True)
            ),
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in courses.order_by('grade_level', 'name')
            ],
        )

    def get_work_analysis_source(self, year):
        events, participations, courses = self._get_event_scope(year)
        scoped_participations = list(
            participations.select_related('event').only(
                'pk',
                'event_id',
                'event__work_id',
            )
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in scoped_participations),
            include_task_results=False,
        )
        attempts_by_work = defaultdict(list)
        for participation in scoped_participations:
            attempt = attempts.get(participation.pk)
            if attempt is not None and attempt.score is not None:
                attempts_by_work[participation.event.work_id].append(attempt)

        work_sources = []
        for work in Work.objects.all():
            work_events = list(
                self._event_summary_queryset(
                    events.filter(work=work),
                ).order_by('-planned_date')
            )
            if not work_events:
                continue

            work_sources.append(
                WorkAnalysisItemSource(
                    work=self._report_work_ref(work),
                    events_count=len(work_events),
                    marks=[
                        ReportMarkFact(
                            score=attempt.score,
                            points=attempt.points,
                            max_points=attempt.max_points,
                        )
                        for attempt in attempts_by_work[work.pk]
                    ],
                    events=[
                        self._report_event_ref(event)
                        for event in work_events
                    ],
                ),
            )

        return WorkAnalysisSource(
            works=work_sources,
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in courses.order_by('grade_level', 'name')
            ],
        )

    def get_student_performance_source(self, year, group_id):
        _, participations, courses = self._get_event_scope(year)
        groups, students = self._get_student_scope(year)
        groups = groups.order_by('name')

        selected_group = None
        if group_id:
            selected_group = groups.filter(pk=group_id).first()
            if selected_group:
                students = selected_group.students.all()

        students = list(students.order_by('last_name', 'first_name'))
        student_ids = [student.pk for student in students]
        scoped_participations = list(
            participations.filter(
                student_id__in=student_ids,
            ).only('pk', 'student_id', 'status', 'created_at')
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in scoped_participations),
            include_task_results=False,
        )
        participations_by_student = defaultdict(list)
        marks_by_student = defaultdict(list)
        for participation in scoped_participations:
            participations_by_student[participation.student_id].append(
                StudentPerformanceParticipationFact(
                    status=participation.status,
                    created_at=participation.created_at,
                )
            )
            attempt = attempts.get(participation.pk)
            if attempt is None or attempt.score is None:
                continue
            marks_by_student[participation.student_id].append(
                ReportMarkFact(
                    score=attempt.score,
                    points=attempt.points,
                    max_points=attempt.max_points,
                )
            )

        return StudentPerformanceSource(
            students=[
                StudentPerformanceItemSource(
                    student=self._report_student_ref(student),
                    participations=participations_by_student[student.pk],
                    marks=marks_by_student[student.pk],
                )
                for student in students
                if participations_by_student[student.pk]
            ],
            groups=[
                ReportGroupRef(
                    pk=str(group.pk),
                    name=group.name,
                    students_count=group.students.count(),
                )
                for group in groups
            ],
            selected_group=(
                ReportGroupRef(
                    pk=str(selected_group.pk),
                    name=selected_group.name,
                    students_count=selected_group.students.count(),
                )
                if selected_group
                else None
            ),
            courses=[
                ReportCourseRef(pk=str(course.pk), name=course.name)
                for course in courses.order_by('grade_level', 'name')
            ],
        )

    @staticmethod
    def _get_event_scope(year):
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

    @staticmethod
    def _get_student_scope(year):
        if year:
            return (
                StudentGroup.objects.filter(academic_year_id=year.pk),
                Student.objects.filter(
                    studentgroup__academic_year_id=year.pk,
                ).distinct(),
            )
        return StudentGroup.objects.all(), Student.objects.all()

    @staticmethod
    def _report_student_ref(student):
        return ReportStudentRef(
            pk=str(student.pk),
            full_name=student.get_full_name(),
            short_name=student.get_short_name(),
            last_name=student.last_name,
            first_name=student.first_name,
        )

    def _report_event_ref(self, event):
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
            work=self._report_work_ref(event.work),
            participants_count=event.participants_count_value,
            graded_count=event.graded_count_value,
            progress_percentage=progress_percentage,
        )

    @staticmethod
    def _event_summary_queryset(queryset):
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

    @staticmethod
    def _report_work_ref(work):
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
