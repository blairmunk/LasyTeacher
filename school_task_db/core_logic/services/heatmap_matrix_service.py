"""Pure aggregation for student performance matrices."""

from collections import defaultdict

from core_logic.entities.report import (
    HeatmapMatrixSource,
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
    def build_topic_matrix(
        self,
        source: HeatmapMatrixSource,
    ) -> HeatmapTopicMatrixData:
        if not source.columns:
            return HeatmapTopicMatrixData(
                columns=[],
                rows=[],
                col_averages=[],
            )

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
                    cells.append({
                        'pct': pct,
                        'points': data['points'],
                        'max_points': data['max_points'],
                        'css': self.color_class(pct),
                        'topic': column,
                    })
                else:
                    cells.append({
                        'pct': None,
                        'css': 'no-data',
                        'topic': column,
                    })

            avg = round(total_points / total_max * 100) if total_max > 0 else None
            rows.append({
                'student': student,
                'cells': cells,
                'avg': avg,
                'avg_css': self.color_class(avg),
            })

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
            col_averages.append({
                'pct': avg,
                'css': self.color_class(avg),
            })

        return HeatmapTopicMatrixData(
            columns=source.columns,
            rows=rows,
            col_averages=col_averages,
        )

    @staticmethod
    def color_class(pct):
        return performance_color_class(pct)
