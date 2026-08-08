"""Pure calculations for the reports dashboard."""

from collections import Counter
from datetime import timedelta

from core_logic.entities.report_summary import (
    ReportsDashboardData,
    ReportsDashboardSource,
)


class ReportsDashboardService:
    def build(
        self,
        source: ReportsDashboardSource,
        current_date,
    ) -> ReportsDashboardData:
        scores = [mark.score for mark in source.marks if mark.score is not None]
        score_counts = Counter(scores)
        event_by_id = {event.pk: event for event in source.events}
        monthly_labels, monthly_values = self._monthly_activity(
            source.participations,
            event_by_id,
            current_date,
        )
        class_stats = [
            self._group_stat(group, source)
            for group in source.groups
        ]
        event_status_counts = Counter(event.status for event in source.events)
        marks_by_event = {}
        for event in source.events:
            event_scores = [
                mark.score
                for mark in source.marks
                if mark.event_id == event.pk and mark.score is not None
            ]
            if event_scores:
                work_name = event.work.name if event.work else 'Без работы'
                marks_by_event[work_name[:20]] = event_scores

        return ReportsDashboardData(
            total_students=source.total_students,
            total_events=len(source.events),
            total_works=source.total_works,
            total_courses=len(source.courses),
            total_marks=len(source.marks),
            average_score=(sum(scores) / len(scores) if scores else 0),
            marks_last_month=sum(
                1
                for mark in source.marks
                if mark.checked_at is not None
                and mark.checked_at >= current_date - timedelta(days=30)
            ),
            score_counts=dict(score_counts),
            events_planned=event_status_counts['planned'],
            events_completed=event_status_counts['completed'],
            events_graded=event_status_counts['graded'],
            monthly_labels=monthly_labels,
            monthly_values=monthly_values,
            class_stats=class_stats,
            class_names=[stat['name'] for stat in class_stats],
            class_avg_scores=[stat['average_score'] for stat in class_stats],
            class_completion=[stat['completion_rate'] for stat in class_stats],
            recent_events=source.events[:10],
            event_status_counts=dict(event_status_counts),
            box_data=marks_by_event,
            courses=source.courses,
        )

    @staticmethod
    def _monthly_activity(participations, event_by_id, current_date):
        labels = []
        values = []
        for index in range(6):
            month_start = current_date.replace(day=1) - timedelta(
                days=30 * index,
            )
            month_end = month_start + timedelta(days=31)
            values.append(sum(
                1
                for participation in participations
                if participation.status in ('completed', 'graded')
                and participation.event_id in event_by_id
                and month_start
                <= event_by_id[participation.event_id].planned_date
                <= month_end
            ))
            labels.append(month_start.strftime('%b %Y'))
        labels.reverse()
        values.reverse()
        return labels, values

    @staticmethod
    def _group_stat(group_source, source):
        student_ids = set(group_source.student_ids)
        participations = [
            participation
            for participation in source.participations
            if participation.student_id in student_ids
        ]
        marks = [
            mark
            for mark in source.marks
            if mark.student_id in student_ids and mark.score is not None
        ]
        completed_count = sum(
            1
            for participation in participations
            if participation.status in ('completed', 'graded')
        )
        average_score = (
            round(sum(mark.score for mark in marks) / len(marks), 2)
            if marks
            else 0
        )
        total_participations = len(participations)
        return {
            'name': group_source.group.name,
            'students_count': group_source.group.students_count,
            'total_participations': total_participations,
            'completed_participations': completed_count,
            'average_score': average_score,
            'completion_rate': round(
                completed_count / total_participations * 100
                if total_participations > 0
                else 0,
                1,
            ),
            'id': group_source.group.pk,
            'heatmap_links': [
                {
                    'course_id': link.course_id,
                    'course_name': link.course_name,
                    'group_id': link.group_id,
                    'group_name': link.group_name,
                }
                for link in group_source.course_links
            ],
        }
