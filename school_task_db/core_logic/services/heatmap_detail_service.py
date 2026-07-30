"""Pure calculations for detailed performance reports."""

from collections import defaultdict

from core_logic.entities.report import (
    HeatmapStudentDetailData,
    HeatmapStudentDetailSource,
    HeatmapSubtopicDetailData,
    HeatmapSubtopicDetailSource,
)
from core_logic.services.heatmap_matrix_service import performance_color_class


class HeatmapDetailService:
    def build_student_detail(
        self,
        source: HeatmapStudentDetailSource,
    ) -> HeatmapStudentDetailData:
        tasks_by_id = {
            task.pk: task
            for task in source.tasks
        }
        subtopics_by_id = {
            subtopic.pk: subtopic
            for subtopic in source.subtopics
        }
        selected_subtopic_id = (
            source.selected_subtopic.pk
            if source.selected_subtopic
            else ''
        )

        details = []
        aggregated = defaultdict(lambda: {'points': 0, 'max_points': 0})
        for score in source.scores:
            if score.subtopic_id:
                aggregated[score.subtopic_id]['points'] += score.points
                aggregated[score.subtopic_id]['max_points'] += score.max_points

            if (
                selected_subtopic_id
                and score.subtopic_id != selected_subtopic_id
            ):
                continue
            task = tasks_by_id.get(score.task_id)
            if not task:
                continue
            subtopic = subtopics_by_id.get(score.subtopic_id)
            pct = (
                round(score.points / score.max_points * 100)
                if score.max_points > 0
                else 0
            )
            details.append({
                'event': score.event,
                'task': task,
                'subtopic': subtopic,
                'points': score.points,
                'max_points': score.max_points,
                'pct': pct,
                'css': performance_color_class(pct),
            })

        details.sort(key=lambda detail: (
            detail['subtopic'].name if detail['subtopic'] else '',
            detail['event'] is None,
            detail['event'].planned_date if detail['event'] else None,
        ))

        subtopic_summary = []
        for subtopic in source.subtopics:
            data = aggregated.get(subtopic.pk)
            is_selected = subtopic.pk == selected_subtopic_id
            if data and data['max_points'] > 0:
                pct = round(data['points'] / data['max_points'] * 100)
                subtopic_summary.append({
                    'subtopic': subtopic,
                    'points': data['points'],
                    'max_points': data['max_points'],
                    'pct': pct,
                    'css': performance_color_class(pct),
                    'is_selected': is_selected,
                })
            else:
                subtopic_summary.append({
                    'subtopic': subtopic,
                    'pct': None,
                    'css': 'no-data',
                    'is_selected': is_selected,
                })

        return HeatmapStudentDetailData(
            topic=source.topic,
            student=source.student,
            selected_subtopic=source.selected_subtopic,
            details=details,
            subtopic_summary=subtopic_summary,
            courses=source.courses,
        )

    def build_subtopic_detail(
        self,
        source: HeatmapSubtopicDetailSource,
    ) -> HeatmapSubtopicDetailData:
        student_agg = defaultdict(
            lambda: {'points': 0, 'max_points': 0, 'events': set()},
        )
        task_agg = defaultdict(
            lambda: {
                'points': 0,
                'max_points': 0,
                'student_ids': set(),
            },
        )

        for score in source.scores:
            student_data = student_agg[score.student_id]
            student_data['points'] += score.points
            student_data['max_points'] += score.max_points
            if score.event:
                student_data['events'].add(score.event.name)

            task_data = task_agg[score.task_id]
            task_data['points'] += score.points
            task_data['max_points'] += score.max_points
            task_data['student_ids'].add(score.student_id)

        student_rows = []
        for student in source.students:
            data = student_agg.get(student.pk)
            if data and data['max_points'] > 0:
                pct = round(data['points'] / data['max_points'] * 100)
                student_rows.append({
                    'student': student,
                    'points': data['points'],
                    'max_points': data['max_points'],
                    'pct': pct,
                    'css': performance_color_class(pct),
                    'events': sorted(data['events']),
                })
            else:
                student_rows.append({
                    'student': student,
                    'pct': None,
                    'css': 'no-data',
                    'events': [],
                })

        task_rows = []
        for task in source.tasks:
            data = task_agg.get(task.pk)
            if not data or data['max_points'] <= 0:
                continue
            avg_pct = round(data['points'] / data['max_points'] * 100)
            task_rows.append({
                'task': task,
                'avg_pct': avg_pct,
                'css': performance_color_class(avg_pct),
                'students_count': len(data['student_ids']),
                'total_points': data['points'],
                'total_max': data['max_points'],
            })

        total_points = sum(data['points'] for data in student_agg.values())
        total_max = sum(data['max_points'] for data in student_agg.values())
        overall_pct = (
            round(total_points / total_max * 100)
            if total_max > 0
            else None
        )

        return HeatmapSubtopicDetailData(
            subtopic=source.subtopic,
            topic=source.topic,
            groups=source.groups,
            selected_group=source.selected_group,
            student_rows=student_rows,
            task_rows=task_rows,
            overall_pct=overall_pct,
            overall_css=performance_color_class(overall_pct),
            total_students=len(source.students),
            students_with_data=sum(
                1
                for row in student_rows
                if row['pct'] is not None
            ),
            courses=source.courses,
        )
