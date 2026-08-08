from unittest import TestCase

from datetime import datetime

from core_logic.entities.heatmap import (
    HeatmapCourseTimelineSource,
    HeatmapTimelineEventRef,
    HeatmapTimelineMarkFact,
)
from core_logic.use_cases.get_heatmap_course_timeline import (
    GetHeatmapCourseTimelineUseCase,
    HeatmapCourseTimelineRequest,
)


class FakeReportRepository:
    def __init__(self):
        self.student_ids = None
        self.work_ids = None

    def get_heatmap_course_timeline_source(self, student_ids, work_ids):
        self.student_ids = student_ids
        self.work_ids = work_ids
        return HeatmapCourseTimelineSource(
            events=[
                HeatmapTimelineEventRef(
                    pk='event-1',
                    name='КР',
                    planned_date=datetime(2026, 1, 1),
                ),
            ],
            marks=[
                HeatmapTimelineMarkFact(
                    event_id='event-1',
                    points=8,
                    max_points=10,
                ),
            ],
        )


class GetHeatmapCourseTimelineUseCaseTests(TestCase):
    def test_execute_returns_repository_timeline_data(self):
        repo = FakeReportRepository()
        use_case = GetHeatmapCourseTimelineUseCase(report_repo=repo)

        data = use_case.execute(
            HeatmapCourseTimelineRequest(
                student_ids=['student-1'],
                work_ids=['work-1'],
            ),
        )

        self.assertEqual(repo.student_ids, ['student-1'])
        self.assertEqual(repo.work_ids, ['work-1'])
        self.assertEqual(data.dates, ['2026-01-01'])
        self.assertEqual(data.averages, [80])
        self.assertEqual(data.labels, ['КР'])
