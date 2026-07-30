from unittest import TestCase

from core_logic.entities.report import (
    HeatmapDetailScoreFact,
    HeatmapSubtopicDetailSource,
    ReportCourseRef,
    ReportGroupRef,
    ReportHeatmapColumnRef,
    ReportStudentRef,
    ReportTaskRef,
)
from core_logic.use_cases.get_heatmap_subtopic_detail import (
    GetHeatmapSubtopicDetailUseCase,
    HeatmapSubtopicDetailRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.subtopic_id = None
        self.group_id = None

    def get_heatmap_subtopic_detail_source(self, subtopic_id, group_id):
        self.subtopic_id = subtopic_id
        self.group_id = group_id
        student = ReportStudentRef(
            pk='student-1',
            full_name='Иванов Иван',
        )
        task = ReportTaskRef(
            pk='task-1',
            text='Задача',
            difficulty=2,
            difficulty_display='Базовая',
        )
        return HeatmapSubtopicDetailSource(
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
            students=[student],
            tasks=[task],
            scores=[
                HeatmapDetailScoreFact(
                    student_id=student.pk,
                    task_id=task.pk,
                    subtopic_id='subtopic-1',
                    points=8,
                    max_points=10,
                ),
            ],
            courses=[ReportCourseRef(pk='course-1', name='Физика 7')],
        )


class GetHeatmapSubtopicDetailUseCaseTests(TestCase):
    def test_execute_returns_repository_detail_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapSubtopicDetailUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapSubtopicDetailRequest(
                subtopic_id='subtopic-1',
                group_id='group-1',
            ),
        )

        self.assertEqual(repo.subtopic_id, 'subtopic-1')
        self.assertEqual(repo.group_id, 'group-1')
        self.assertEqual(data.student_rows[0]['pct'], 80)
        self.assertEqual(data.task_rows[0]['avg_pct'], 80)
        self.assertEqual(data.active_report, 'heatmap')
