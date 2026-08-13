"""Pure aggregation for student performance matrices."""

from collections import defaultdict

from core_logic.entities.heatmap import (
    HeatmapColumnAverage,
    HeatmapCourseTimelineData,
    HeatmapCourseTimelineSource,
    HeatmapMatrixCell,
    HeatmapMatrixRow,
    HeatmapMatrixSource,
    HeatmapSubtopicMatrixData,
    HeatmapTopicMatrixData,
)


def performance_color_class(pct):
    if pct is None:
        return 'no-data'
    if pct >= 95:
        return 'perfect'
    if pct >= 85:
        return 'excellent'
    if pct >= 70:
        return 'good'
    if pct >= 60:
        return 'moderate'
    if pct >= 45:
        return 'warning'
    return 'danger'


class HeatmapMatrixService:
    def build_course_timeline(
        self,
        source: HeatmapCourseTimelineSource,
    ) -> HeatmapCourseTimelineData:
        marks_by_event = defaultdict(list)
        for mark in source.marks:
            marks_by_event[mark.event_id].append(mark)

        dates = []
        averages = []
        labels = []
        for event in source.events:
            marks = marks_by_event[event.pk]
            total_points = sum(mark.points for mark in marks)
            total_max = sum(mark.max_points for mark in marks)
            if total_max <= 0:
                continue
            dates.append(event.planned_date.strftime('%Y-%m-%d'))
            averages.append(round(total_points / total_max * 100))
            labels.append(event.name)

        return HeatmapCourseTimelineData(
            dates=tuple(dates),
            averages=tuple(averages),
            labels=tuple(labels),
        )

    def build_topic_matrix(
        self,
        source: HeatmapMatrixSource,
    ) -> HeatmapTopicMatrixData:
        columns, rows, col_averages = self._build_matrix(source)
        return HeatmapTopicMatrixData(
            columns=columns,
            rows=rows,
            col_averages=col_averages,
        )

    def build_subtopic_matrix(
        self,
        source: HeatmapMatrixSource,
    ) -> HeatmapSubtopicMatrixData:
        columns, rows, col_averages = self._build_matrix(source)
        return HeatmapSubtopicMatrixData(
            columns=columns,
            rows=rows,
            col_averages=col_averages,
        )

    def _build_matrix(self, source: HeatmapMatrixSource):
        if not source.columns:
            return (), (), ()

        aggregated = defaultdict(lambda: {'points': 0, 'max_points': 0})
        for score in source.scores:
            key = (score.student_id, score.column_id)
            aggregated[key]['points'] += score.points
            aggregated[key]['max_points'] += score.max_points

        rows = []
        for student in source.students:
            cells = []
            total_points = 0
            total_max = 0
            for column in source.columns:
                data = aggregated.get((student.pk, column.pk))
                if data and data['max_points'] > 0:
                    pct = round(data['points'] / data['max_points'] * 100)
                    total_points += data['points']
                    total_max += data['max_points']
                    cells.append(HeatmapMatrixCell(
                        column=column,
                        pct=pct,
                        points=data['points'],
                        max_points=data['max_points'],
                        css=self.color_class(pct),
                    ))
                else:
                    cells.append(HeatmapMatrixCell(
                        column=column,
                        pct=None,
                        css='no-data',
                    ))

            avg = round(total_points / total_max * 100) if total_max > 0 else None
            rows.append(HeatmapMatrixRow(
                student=student,
                cells=tuple(cells),
                avg=avg,
                avg_css=self.color_class(avg),
            ))

        col_averages = []
        for column in source.columns:
            points = sum(
                aggregated.get((student.pk, column.pk), {}).get('points', 0)
                for student in source.students
            )
            max_points = sum(
                aggregated.get((student.pk, column.pk), {}).get('max_points', 0)
                for student in source.students
            )
            avg = round(points / max_points * 100) if max_points > 0 else None
            col_averages.append(HeatmapColumnAverage(
                pct=avg,
                css=self.color_class(avg),
            ))

        return source.columns, tuple(rows), tuple(col_averages)

    @staticmethod
    def color_class(pct):
        return performance_color_class(pct)
