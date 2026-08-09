"""Django read adapter for the class journal."""

from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from core_logic.entities.journal import (
    JournalEntryFact,
    JournalParticipationRef,
    JournalSelectData,
    JournalSource,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportEventRef,
    ReportGroupRef,
    ReportMarkFact,
    ReportStudentRef,
    ReportVariantRef,
    ReportWorkRef,
)
from core_logic.interfaces.journal_repo import IJournalRepository
from core_logic.services.event_service import EventService
from curriculum.models import Course
from events.models import Event, EventParticipation
from infrastructure.services.django_attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from students.models import StudentGroup


class DjangoJournalRepository(IJournalRepository):
    def get_journal_select(self, year):
        courses = self._course_scope(year).order_by('grade_level', 'name')
        groups = self._group_scope(year).order_by('name')
        available_group_ids = set(groups.values_list('pk', flat=True))

        journal_links = []
        for course in courses:
            for group in course.student_groups.filter(
                pk__in=available_group_ids,
            ):
                event_count = Event.objects.filter(
                    course=course,
                    eventparticipation__student__in=group.students.all(),
                ).distinct().count()
                journal_links.append({
                    'course': self._course_ref(course),
                    'group': self._group_ref(group),
                    'event_count': event_count,
                })

        return JournalSelectData(
            journal_links=journal_links,
            groups=[self._group_ref(group) for group in groups],
            courses=[self._course_ref(course) for course in courses],
        )

    def get_journal_source(self, course_id, group_id, year):
        course = get_object_or_404(Course, pk=course_id)
        group = get_object_or_404(StudentGroup, pk=group_id)
        students = list(
            group.students.all().order_by('last_name', 'first_name')
        )
        student_ids = [student.id for student in students]

        event_ids = Event.objects.filter(
            course=course,
            eventparticipation__student__in=student_ids,
        ).values_list('pk', flat=True).distinct()
        events = list(self._event_summary_queryset(
            Event.objects.filter(pk__in=event_ids),
        ).order_by('planned_date'))
        event_refs = {
            event.id: self._event_ref(event)
            for event in events
        }
        participations = list(
            EventParticipation.objects.filter(
                event__in=events,
                student_id__in=student_ids,
            ).select_related('student', 'event', 'variant')
        )
        attempts = latest_attempts_by_participation(
            (participation.pk for participation in participations),
            include_task_results=False,
        )
        entries = []
        for participation in participations:
            attempt = attempts.get(participation.id)
            entries.append(JournalEntryFact(
                student_id=str(participation.student_id),
                event_id=str(participation.event_id),
                participation=JournalParticipationRef(
                    pk=str(participation.pk),
                    status=participation.status,
                ),
                mark=(
                    ReportMarkFact(
                        score=attempt.score,
                        points=attempt.points,
                        max_points=attempt.max_points,
                    )
                    if attempt
                    else None
                ),
                variant=(
                    self._attempt_variant_ref(attempt)
                    if attempt and attempt.variant_id_snapshot
                    else (
                        self._variant_ref(participation.variant)
                        if participation.variant
                        else None
                    )
                ),
            ))

        return JournalSource(
            course=self._course_ref(course),
            group=ReportGroupRef(
                pk=str(group.pk),
                name=group.name,
                students_count=len(students),
            ),
            students=[self._student_ref(student) for student in students],
            events=[event_refs[event.id] for event in events],
            entries=entries,
            courses=[
                self._course_ref(item)
                for item in self._course_scope(year).order_by(
                    'grade_level',
                    'name',
                )
            ],
        )

    @staticmethod
    def _course_scope(year):
        if year:
            return Course.objects.filter(year_id=year.pk, is_active=True)
        return Course.objects.filter(is_active=True)

    @staticmethod
    def _group_scope(year):
        if year:
            return StudentGroup.objects.filter(academic_year_id=year.pk)
        return StudentGroup.objects.all()

    @staticmethod
    def _student_ref(student):
        return ReportStudentRef(
            pk=str(student.pk),
            full_name=student.get_full_name(),
            short_name=student.get_short_name(),
            last_name=student.last_name,
            first_name=student.first_name,
        )

    @staticmethod
    def _group_ref(group):
        return ReportGroupRef(
            pk=str(group.pk),
            name=group.name,
            students_count=group.students.count(),
        )

    @staticmethod
    def _course_ref(course):
        return ReportCourseRef(pk=str(course.pk), name=course.name)

    def _event_ref(self, event):
        return ReportEventRef(
            pk=str(event.pk),
            name=event.name,
            status=event.status,
            status_display=event.get_status_display(),
            planned_date=event.planned_date,
            actual_end=event.actual_end,
            location=event.location,
            work=self._work_ref(event.work),
            participants_count=event.participants_count_value,
            graded_count=event.graded_count_value,
            progress_percentage=EventService.progress_percentage(
                event.participants_count_value,
                event.completed_count_value,
            ),
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
    def _work_ref(work):
        return ReportWorkRef(
            pk=str(work.pk),
            name=work.name,
            work_type=work.work_type,
            work_type_display=work.get_work_type_display(),
            duration=work.duration,
            variant_count=work.variant_set.count(),
        )

    @staticmethod
    def _variant_ref(variant):
        return ReportVariantRef(
            pk=str(variant.pk),
            short_uuid=variant.get_short_uuid(),
            number=variant.number,
            work_name_snapshot=variant.work_name_snapshot,
        )

    @staticmethod
    def _attempt_variant_ref(attempt):
        variant_id = attempt.variant_id_snapshot
        return ReportVariantRef(
            pk=variant_id,
            short_uuid=variant_id[-4:].upper(),
            number=attempt.variant_number_snapshot,
            work_name_snapshot=attempt.work_name_snapshot,
        )
