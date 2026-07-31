"""Pure calculations for summary reports."""

from collections import Counter
from datetime import timedelta

from core_logic.entities.report import (
    EventsStatusReportData,
    EventsStatusSource,
    StudentPerformanceReportData,
    StudentPerformanceSource,
    WorkAnalysisReportData,
    WorkAnalysisSource,
)


class ReportSummaryService:
    def build_events_status(
        self,
        source: EventsStatusSource,
        current_date,
    ) -> EventsStatusReportData:
        event_counts = Counter(event.status for event in source.events)
        participation_counts = Counter(source.participation_statuses)
        return EventsStatusReportData(
            events_by_status=[
                {'status': status, 'count': event_counts[status]}
                for status in sorted(event_counts)
            ],
            overdue_events=[
                event
                for event in source.events
                if event.status == 'planned'
                and event.planned_date < current_date - timedelta(days=1)
            ],
            long_reviewing=[
                event
                for event in source.events
                if event.status == 'reviewing'
                and event.actual_end is not None
                and event.actual_end < current_date - timedelta(days=7)
            ],
            completed_unchecked=[
                event
                for event in source.events
                if event.status == 'completed'
                and event.actual_end is not None
                and event.actual_end < current_date - timedelta(days=3)
            ],
            participation_stats=[
                {'status': status, 'count': participation_counts[status]}
                for status in sorted(participation_counts)
            ],
            all_events=source.events,
            courses=source.courses,
        )

    def build_student_performance(
        self,
        source: StudentPerformanceSource,
    ) -> StudentPerformanceReportData:
        students_stats = []
        for item in source.students:
            total_participations = len(item.participations)
            if total_participations == 0:
                continue
            completed_count = sum(
                1
                for participation in item.participations
                if participation.status in ('completed', 'graded')
            )
            scores = [
                mark.score
                for mark in item.marks
                if mark.score is not None
            ]
            total_points = sum(mark.points or 0 for mark in item.marks)
            total_max = sum(mark.max_points or 0 for mark in item.marks)
            students_stats.append({
                'student': item.student,
                'total_participations': total_participations,
                'completed_participations': completed_count,
                'completion_rate': round(
                    completed_count / total_participations * 100,
                    1,
                ),
                'total_marks': len(item.marks),
                'average_score': (
                    round(sum(scores) / len(scores), 2)
                    if scores
                    else 0
                ),
                'average_pct': (
                    round(total_points / total_max * 100)
                    if total_max > 0
                    else None
                ),
                'last_activity': max(
                    item.participations,
                    key=lambda participation: participation.created_at,
                ),
            })

        percentages = [
            stat['average_pct']
            for stat in students_stats
            if stat['average_pct'] is not None
        ]
        return StudentPerformanceReportData(
            students_stats=students_stats,
            groups=source.groups,
            selected_group=source.selected_group,
            summary_stats={
                'total_students': len(students_stats),
                'high_performers': sum(
                    1
                    for stat in students_stats
                    if (stat['average_pct'] or 0) >= 85
                ),
                'need_attention': sum(
                    1
                    for stat in students_stats
                    if stat['average_pct'] is not None
                    and stat['average_pct'] < 45
                ),
                'avg_completion_rate': (
                    round(
                        sum(
                            stat['completion_rate']
                            for stat in students_stats
                        ) / len(students_stats),
                        1,
                    )
                    if students_stats
                    else 0
                ),
                'avg_pct': (
                    round(sum(percentages) / len(percentages))
                    if percentages
                    else 0
                ),
            },
            courses=source.courses,
        )

    def build_work_analysis(
        self,
        source: WorkAnalysisSource,
    ) -> WorkAnalysisReportData:
        works_analysis = []
        for item in source.works:
            scores = [
                mark.score
                for mark in item.marks
                if mark.score is not None
            ]
            average_score = (
                round(sum(scores) / len(scores), 2)
                if scores
                else 0
            )
            total_points = sum(mark.points or 0 for mark in item.marks)
            total_max = sum(mark.max_points or 0 for mark in item.marks)
            average_percentage = (
                round(total_points / total_max * 100)
                if total_max > 0
                else 0
            )
            score_counts = Counter(scores)
            score_distribution = [
                {'score': score, 'count': score_counts[score]}
                for score in sorted(score_counts)
            ]

            works_analysis.append({
                'work': item.work,
                'events_count': item.events_count,
                'total_marks': len(item.marks),
                'average_score': average_score,
                'average_percentage': average_percentage,
                'score_distribution': score_distribution,
                'difficulty_assessment': self.assess_difficulty(
                    average_percentage,
                ),
            })

        return WorkAnalysisReportData(
            works_analysis=works_analysis,
            summary_stats={
                'total_works': len(works_analysis),
                'total_marks': sum(
                    work['total_marks']
                    for work in works_analysis
                ),
                'easy_works': sum(
                    1
                    for work in works_analysis
                    if work['difficulty_assessment'] == 'Легкая'
                ),
                'hard_works': sum(
                    1
                    for work in works_analysis
                    if work['difficulty_assessment'] in (
                        'Сложная',
                        'Очень сложная',
                    )
                ),
                'avg_score': (
                    round(
                        sum(
                            work['average_score']
                            for work in works_analysis
                        ) / len(works_analysis),
                        2,
                    )
                    if works_analysis
                    else 0
                ),
            },
            courses=source.courses,
        )

    @staticmethod
    def assess_difficulty(average_percentage):
        if average_percentage >= 85:
            return 'Легкая'
        if average_percentage >= 70:
            return 'Средняя'
        if average_percentage >= 50:
            return 'Сложная'
        return 'Очень сложная'
