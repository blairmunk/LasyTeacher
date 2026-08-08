"""Pure calculations for the student performance report."""

from core_logic.entities.report_summary import (
    StudentPerformanceReportData,
    StudentPerformanceSource,
)


class StudentPerformanceService:
    def build(
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
