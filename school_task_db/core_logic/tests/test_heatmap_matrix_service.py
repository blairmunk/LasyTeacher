from unittest import TestCase

from core_logic.entities.report import (
    HeatmapMatrixSource,
    HeatmapScoreFact,
    ReportHeatmapColumnRef,
    ReportStudentRef,
)
from core_logic.services.heatmap_matrix_service import (
    HeatmapMatrixService,
    performance_color_class,
)


class HeatmapMatrixServiceTests(TestCase):
    def test_aggregates_score_facts_by_student_and_column(self):
        source = HeatmapMatrixSource(
            students=[
                ReportStudentRef(
                    pk='student-1',
                    full_name='Иванов Иван',
                    short_name='Иванов И.',
                ),
                ReportStudentRef(
                    pk='student-2',
                    full_name='Петров Пётр',
                    short_name='Петров П.',
                ),
            ],
            columns=[
                ReportHeatmapColumnRef(
                    pk='topic-1',
                    name='Кинематика',
                    section='Механика',
                ),
                ReportHeatmapColumnRef(
                    pk='topic-2',
                    name='Динамика',
                    section='Механика',
                ),
            ],
            scores=[
                HeatmapScoreFact('student-1', 'topic-1', 3, 5),
                HeatmapScoreFact('student-1', 'topic-1', 4, 5),
                HeatmapScoreFact('student-2', 'topic-1', 5, 5),
            ],
        )

        data = HeatmapMatrixService().build_topic_matrix(source)

        self.assertEqual(data.rows[0]['cells'][0]['points'], 7)
        self.assertEqual(data.rows[0]['cells'][0]['max_points'], 10)
        self.assertEqual(data.rows[0]['cells'][0]['pct'], 70)
        self.assertEqual(data.rows[0]['avg'], 70)
        self.assertEqual(data.rows[0]['cells'][1]['pct'], None)
        self.assertEqual(data.rows[0]['cells'][1]['css'], 'no-data')
        self.assertEqual(data.rows[1]['avg'], 100)
        self.assertEqual(data.col_averages[0], {
            'pct': 80,
            'css': 'good',
        })
        self.assertEqual(data.col_averages[1], {
            'pct': None,
            'css': 'no-data',
        })

    def test_returns_empty_matrix_when_source_has_no_columns(self):
        source = HeatmapMatrixSource(
            students=[
                ReportStudentRef(pk='student-1', full_name='Иванов Иван'),
            ],
            columns=[],
            scores=[],
        )

        data = HeatmapMatrixService().build_topic_matrix(source)

        self.assertEqual(data.columns, [])
        self.assertEqual(data.rows, [])
        self.assertEqual(data.col_averages, [])

    def test_performance_color_thresholds_are_domain_owned(self):
        cases = (
            (None, 'no-data'),
            (95, 'perfect'),
            (85, 'excellent'),
            (70, 'good'),
            (60, 'moderate'),
            (45, 'warning'),
            (44, 'danger'),
        )

        for percentage, expected in cases:
            with self.subTest(percentage=percentage):
                self.assertEqual(
                    performance_color_class(percentage),
                    expected,
                )
