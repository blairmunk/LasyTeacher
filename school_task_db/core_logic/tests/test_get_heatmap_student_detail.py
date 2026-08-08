from unittest import TestCase

from core_logic.entities.heatmap import (
    HeatmapDetailScoreFact,
    HeatmapStudentDetailSource,
    ReportHeatmapColumnRef,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportStudentRef,
    ReportTaskRef,
)
from core_logic.use_cases.get_heatmap_student_detail import (
    GetHeatmapStudentDetailUseCase,
    HeatmapStudentDetailRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.topic_id = None
        self.student_id = None
        self.subtopic_id = None

    def get_heatmap_student_detail_source(
        self,
        topic_id,
        student_id,
        subtopic_id,
    ):
        self.topic_id = topic_id
        self.student_id = student_id
        self.subtopic_id = subtopic_id
        subtopic = ReportHeatmapColumnRef(
            pk='subtopic-1',
            name='Средняя скорость',
        )
        task = ReportTaskRef(
            pk='task-1',
            text='Задача',
            difficulty=2,
            difficulty_display='Базовая',
        )
        return HeatmapStudentDetailSource(
            topic=ReportHeatmapColumnRef(
                pk='topic-1',
                name='Скорость',
                section='Кинематика',
            ),
            student=ReportStudentRef(
                pk='student-1',
                full_name='Иванов Иван',
            ),
            selected_subtopic=subtopic,
            subtopics=[subtopic],
            tasks=[task],
            scores=[
                HeatmapDetailScoreFact(
                    student_id='student-1',
                    task_id=task.pk,
                    subtopic_id=subtopic.pk,
                    points=8,
                    max_points=10,
                ),
            ],
            courses=[ReportCourseRef(pk='course-1', name='Физика 7')],
        )


class GetHeatmapStudentDetailUseCaseTests(TestCase):
    def test_execute_returns_repository_detail_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapStudentDetailUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapStudentDetailRequest(
                topic_id='topic-1',
                student_id='student-1',
                subtopic_id='subtopic-1',
            ),
        )

        self.assertEqual(repo.topic_id, 'topic-1')
        self.assertEqual(repo.student_id, 'student-1')
        self.assertEqual(repo.subtopic_id, 'subtopic-1')
        self.assertEqual(data.details[0]['task'].pk, 'task-1')
        self.assertEqual(data.details[0]['pct'], 80)
        self.assertEqual(data.subtopic_summary[0]['pct'], 80)
        self.assertEqual(data.active_report, 'heatmap')
