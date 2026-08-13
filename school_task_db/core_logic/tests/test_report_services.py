from datetime import datetime
from unittest import TestCase

from core_logic.entities.report_summary import (
    EventsStatusSource,
    ReportStatusCount,
    StudentPerformanceItemSource,
    StudentPerformanceParticipationFact,
    StudentPerformanceSource,
    WorkAnalysisItemSource,
    WorkAnalysisSource,
)
from core_logic.entities.report_refs import (
    ReportCourseRef,
    ReportGroupRef,
    ReportEventRef,
    ReportMarkFact,
    ReportStudentRef,
    ReportWorkRef,
)
from core_logic.services.events_status_service import EventsStatusService
from core_logic.services.student_performance_service import (
    StudentPerformanceService,
)
from core_logic.services.work_analysis_service import WorkAnalysisService


class ReportServicesTests(TestCase):
    def test_builds_events_status_and_time_based_attention_lists(self):
        now = datetime(2026, 7, 20, 12, 0)
        source = EventsStatusSource(
            events=[
                self._event(
                    'planned',
                    'planned',
                    now.replace(day=18),
                ),
                self._event(
                    'reviewing',
                    'reviewing',
                    now.replace(day=10),
                    actual_end=now.replace(day=11),
                ),
                self._event(
                    'completed',
                    'completed',
                    now.replace(day=14),
                    actual_end=now.replace(day=16),
                ),
            ],
            participation_statuses=['assigned', 'graded', 'graded'],
            courses=[],
        )

        report = EventsStatusService().build(source, now)

        self.assertEqual(report.events_by_status, (
            ReportStatusCount(status='completed', count=1),
            ReportStatusCount(status='planned', count=1),
            ReportStatusCount(status='reviewing', count=1),
        ))
        self.assertEqual(report.participation_stats, (
            ReportStatusCount(status='assigned', count=1),
            ReportStatusCount(status='graded', count=2),
        ))
        self.assertEqual(report.overdue_events[0].pk, 'planned')
        self.assertEqual(report.long_reviewing[0].pk, 'reviewing')
        self.assertEqual(report.completed_unchecked[0].pk, 'completed')

    def test_builds_student_performance_from_participation_facts(self):
        group = ReportGroupRef(pk='group-1', name='7А')
        latest = StudentPerformanceParticipationFact(
            status='assigned',
            created_at=datetime(2026, 10, 1),
        )
        source = StudentPerformanceSource(
            students=[
                StudentPerformanceItemSource(
                    student=ReportStudentRef(
                        pk='student-1',
                        full_name='Иванов Иван',
                    ),
                    participations=[
                        StudentPerformanceParticipationFact(
                            status='graded',
                            created_at=datetime(2026, 9, 1),
                        ),
                        latest,
                    ],
                    marks=[
                        ReportMarkFact(score=5, points=8, max_points=10),
                        ReportMarkFact(score=4, points=7, max_points=10),
                    ],
                ),
            ],
            groups=[group],
            selected_group=group,
            courses=[],
        )

        report = StudentPerformanceService().build(source)

        stat = report.students_stats[0]
        self.assertEqual(stat.total_participations, 2)
        self.assertEqual(stat.completed_participations, 1)
        self.assertEqual(stat.completion_rate, 50)
        self.assertEqual(stat.average_score, 4.5)
        self.assertEqual(stat.average_pct, 75)
        self.assertEqual(stat.last_activity, latest)
        self.assertEqual(report.summary_stats.total_students, 1)
        self.assertEqual(report.summary_stats.high_performers, 0)
        self.assertEqual(report.summary_stats.need_attention, 0)
        self.assertEqual(report.summary_stats.avg_completion_rate, 50)
        self.assertEqual(report.summary_stats.avg_pct, 75)

    def test_student_without_scored_marks_has_no_average_percentage(self):
        source = StudentPerformanceSource(
            students=[
                StudentPerformanceItemSource(
                    student=ReportStudentRef(
                        pk='student-1',
                        full_name='Иванов Иван',
                    ),
                    participations=[
                        StudentPerformanceParticipationFact(
                            status='completed',
                            created_at=datetime(2026, 9, 1),
                        ),
                    ],
                    marks=[],
                ),
            ],
            groups=[],
            selected_group=None,
            courses=[],
        )

        report = StudentPerformanceService().build(source)

        self.assertIsNone(report.students_stats[0].average_pct)
        self.assertEqual(report.summary_stats.avg_pct, 0)

    def test_builds_work_analysis_from_mark_facts(self):
        source = WorkAnalysisSource(
            works=[
                WorkAnalysisItemSource(
                    work=self._work('work-1', 'Контрольная'),
                    events_count=2,
                    events=[
                        self._event(
                            'event-1',
                            'graded',
                            datetime(2026, 9, 1),
                        ),
                    ],
                    marks=[
                        ReportMarkFact(score=4, points=3, max_points=5),
                        ReportMarkFact(score=5, points=5, max_points=5),
                    ],
                ),
                WorkAnalysisItemSource(
                    work=self._work('work-2', 'Самостоятельная'),
                    events_count=1,
                    marks=[
                        ReportMarkFact(score=2, points=2, max_points=10),
                    ],
                ),
            ],
            courses=[ReportCourseRef(pk='course-1', name='Физика 7')],
        )

        report = WorkAnalysisService().build(source)

        first = report.works_analysis[0]
        self.assertEqual(first.events_count, 2)
        self.assertEqual(first.events[0].pk, 'event-1')
        self.assertEqual(first.total_marks, 2)
        self.assertEqual(first.average_score, 4.5)
        self.assertEqual(first.average_percentage, 80)
        self.assertEqual(first.difficulty_assessment, 'Средняя')
        self.assertEqual(
            [(item.score, item.count) for item in first.score_distribution],
            [(4, 1), (5, 1)],
        )
        self.assertEqual(
            report.works_analysis[1].difficulty_assessment,
            'Очень сложная',
        )
        self.assertEqual(report.summary_stats.total_works, 2)
        self.assertEqual(report.summary_stats.total_marks, 3)
        self.assertEqual(report.summary_stats.hard_works, 1)
        self.assertEqual(report.summary_stats.avg_score, 3.25)

    def test_work_without_marks_has_zero_summary_values(self):
        source = WorkAnalysisSource(
            works=[
                WorkAnalysisItemSource(
                    work=self._work('work-1', 'Контрольная'),
                    events_count=1,
                    marks=[],
                ),
            ],
            courses=[],
        )

        report = WorkAnalysisService().build(source)

        work = report.works_analysis[0]
        self.assertEqual(work.average_score, 0)
        self.assertEqual(work.average_percentage, 0)
        self.assertEqual(work.score_distribution, ())
        self.assertEqual(work.difficulty_assessment, 'Очень сложная')

    @staticmethod
    def _work(pk, name):
        return ReportWorkRef(
            pk=pk,
            name=name,
            work_type='control',
            work_type_display='Контрольная работа',
            duration=45,
        )

    @staticmethod
    def _event(pk, status, planned_date, actual_end=None):
        return ReportEventRef(
            pk=pk,
            name=pk,
            status=status,
            status_display=status,
            planned_date=planned_date,
            work=ReportWorkRef(
                pk='work-1',
                name='Работа',
                work_type='test',
                work_type_display='Работа',
                duration=45,
            ),
            actual_end=actual_end,
        )
