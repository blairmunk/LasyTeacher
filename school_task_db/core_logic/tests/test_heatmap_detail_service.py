from unittest import TestCase

from core_logic.entities.report import (
    HeatmapDetailScoreFact,
    HeatmapSubtopicDetailSource,
    ReportActivityRef,
    ReportCourseRef,
    ReportGroupRef,
    ReportHeatmapColumnRef,
    ReportStudentRef,
    ReportTaskRef,
)
from core_logic.services.heatmap_detail_service import HeatmapDetailService


class HeatmapDetailServiceTests(TestCase):
    def test_builds_subtopic_detail_from_normalized_score_facts(self):
        task = ReportTaskRef(
            pk='task-1',
            text='Задача',
            difficulty=2,
            difficulty_display='Базовая',
        )
        source = HeatmapSubtopicDetailSource(
            subtopic=ReportHeatmapColumnRef(
                pk='subtopic-1',
                name='Средняя скорость',
            ),
            topic=ReportHeatmapColumnRef(
                pk='topic-1',
                name='Скорость',
                section='Кинематика',
            ),
            groups=[ReportGroupRef(pk='group-1', name='7А')],
            selected_group=ReportGroupRef(pk='group-1', name='7А'),
            students=[
                ReportStudentRef(
                    pk='student-1',
                    full_name='Иванов Иван',
                ),
                ReportStudentRef(
                    pk='student-2',
                    full_name='Петров Пётр',
                ),
                ReportStudentRef(
                    pk='student-3',
                    full_name='Сидоров Сидор',
                ),
            ],
            tasks=[task],
            scores=[
                HeatmapDetailScoreFact(
                    'student-1',
                    task.pk,
                    'subtopic-1',
                    3,
                    5,
                    ReportActivityRef('event-1', 'КР 1'),
                ),
                HeatmapDetailScoreFact(
                    'student-1',
                    task.pk,
                    'subtopic-1',
                    5,
                    5,
                    ReportActivityRef('event-2', 'КР 2'),
                ),
                HeatmapDetailScoreFact(
                    'student-2',
                    task.pk,
                    'subtopic-1',
                    2,
                    5,
                    ReportActivityRef('event-1', 'КР 1'),
                ),
            ],
            courses=[ReportCourseRef(pk='course-1', name='Физика 7')],
        )

        detail = HeatmapDetailService().build_subtopic_detail(source)

        self.assertEqual(detail.student_rows[0]['pct'], 80)
        self.assertEqual(detail.student_rows[0]['events'], ['КР 1', 'КР 2'])
        self.assertEqual(detail.student_rows[1]['pct'], 40)
        self.assertIsNone(detail.student_rows[2]['pct'])
        self.assertEqual(detail.task_rows[0]['students_count'], 2)
        self.assertEqual(detail.task_rows[0]['avg_pct'], 67)
        self.assertEqual(detail.overall_pct, 67)
        self.assertEqual(detail.students_with_data, 2)
        self.assertEqual(detail.total_students, 3)
