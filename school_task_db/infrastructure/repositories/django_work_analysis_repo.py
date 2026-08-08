"""Django read adapter for work analysis reports."""

from collections import defaultdict

from core_logic.entities.report_summary import (
    WorkAnalysisItemSource,
    WorkAnalysisSource,
)
from core_logic.entities.report_refs import ReportMarkFact
from core_logic.interfaces.work_analysis_repo import IWorkAnalysisRepository
from infrastructure.repositories.django_report_summary_support import (
    event_scope,
    event_summary_queryset,
    report_course_ref,
    report_event_ref,
    report_work_ref,
)
from infrastructure.services.attempt_snapshot_queries import (
    latest_attempts_by_participation,
)
from works.models import Work


class DjangoWorkAnalysisRepository(IWorkAnalysisRepository):
    def get_work_analysis_source(self, year):
        events, participations, courses = event_scope(year)
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
                event_summary_queryset(
                    events.filter(work=work),
                ).order_by('-planned_date')
            )
            if not work_events:
                continue

            work_sources.append(
                WorkAnalysisItemSource(
                    work=report_work_ref(work),
                    events_count=len(work_events),
                    marks=[
                        ReportMarkFact(
                            score=attempt.score,
                            points=attempt.points,
                            max_points=attempt.max_points,
                        )
                        for attempt in attempts_by_work[work.pk]
                    ],
                    events=[report_event_ref(event) for event in work_events],
                ),
            )

        return WorkAnalysisSource(
            works=work_sources,
            courses=[
                report_course_ref(course)
                for course in courses.order_by('grade_level', 'name')
            ],
        )
