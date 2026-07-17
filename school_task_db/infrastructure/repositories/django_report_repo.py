"""Django implementation of report repository."""

from datetime import timedelta

from django.db.models import Avg, Count

from core_logic.entities.report import EventsStatusReportData, WorkAnalysisReportData
from core_logic.interfaces.report_repo import IReportRepository
from curriculum.models import Course
from events.models import Event, EventParticipation, Mark
from works.models import Work


class DjangoReportRepository(IReportRepository):
    def get_events_status_report(self, year, current_date):
        events, participations, courses = self._get_event_scope(year)

        events_by_status = list(
            events.values('status').annotate(
                count=Count('id'),
            ).order_by('status'),
        )
        participation_stats = list(
            participations.values('status').annotate(
                count=Count('id'),
            ).order_by('status'),
        )

        return EventsStatusReportData(
            events_by_status=events_by_status,
            overdue_events=events.filter(
                status='planned',
                planned_date__lt=current_date - timedelta(days=1),
            ).select_related('work'),
            long_reviewing=events.filter(
                status='reviewing',
                actual_end__lt=current_date - timedelta(days=7),
            ).select_related('work'),
            completed_unchecked=events.filter(
                status='completed',
                actual_end__lt=current_date - timedelta(days=3),
            ).select_related('work'),
            participation_stats=participation_stats,
            all_events=events.select_related('work').order_by('-planned_date'),
            courses=courses.order_by('grade_level', 'name'),
        )

    def get_work_analysis_report(self, year):
        events, _, courses = self._get_event_scope(year)
        marks = self._get_marks_scope(year)

        works_analysis = []
        for work in Work.objects.all():
            work_events = events.filter(work=work)
            work_marks = marks.filter(
                participation__event__work=work,
                score__isnull=False,
            )

            if work_events.count() == 0:
                continue

            avg_score = work_marks.aggregate(avg=Avg('score'))['avg'] or 0
            avg_pct = self._average_task_score_percentage(work_marks)
            score_distribution = list(
                work_marks.values('score').annotate(
                    count=Count('id'),
                ).order_by('score'),
            )

            works_analysis.append({
                'work': work,
                'events_count': work_events.count(),
                'total_marks': work_marks.count(),
                'average_score': round(avg_score, 2),
                'average_percentage': avg_pct,
                'score_distribution': score_distribution,
                'difficulty_assessment': self._assess_difficulty(avg_pct),
            })

        return WorkAnalysisReportData(
            works_analysis=works_analysis,
            summary_stats={
                'total_works': len(works_analysis),
                'total_marks': sum(w['total_marks'] for w in works_analysis),
                'easy_works': sum(
                    1 for w in works_analysis
                    if w['difficulty_assessment'] == 'Легкая'
                ),
                'hard_works': sum(
                    1 for w in works_analysis
                    if w['difficulty_assessment'] in ('Сложная', 'Очень сложная')
                ),
                'avg_score': round(
                    sum(w['average_score'] for w in works_analysis)
                    / len(works_analysis),
                    2,
                ) if works_analysis else 0,
            },
            courses=courses.order_by('grade_level', 'name'),
        )

    def _get_event_scope(self, year):
        if year:
            date_range = (year.start_date, year.end_date)
            events = Event.objects.filter(planned_date__range=date_range)
            participations = EventParticipation.objects.filter(
                event__planned_date__range=date_range,
            )
            courses = Course.objects.filter(year=year, is_active=True)
        else:
            events = Event.objects.all()
            participations = EventParticipation.objects.all()
            courses = Course.objects.filter(is_active=True)

        return events, participations, courses

    def _get_marks_scope(self, year):
        if year:
            date_range = (year.start_date, year.end_date)
            return Mark.objects.filter(
                participation__event__planned_date__range=date_range,
            )
        return Mark.objects.all()

    def _average_task_score_percentage(self, marks):
        total_points = 0
        total_max = 0
        for mark in marks:
            if not mark.task_scores:
                continue
            for scores in mark.task_scores.values():
                total_points += scores.get('points', 0)
                total_max += scores.get('max_points', 0)
        return round(total_points / total_max * 100) if total_max > 0 else 0

    def _assess_difficulty(self, avg_pct):
        if avg_pct >= 85:
            return 'Легкая'
        if avg_pct >= 70:
            return 'Средняя'
        if avg_pct >= 50:
            return 'Сложная'
        return 'Очень сложная'
