from datetime import datetime
from unittest import TestCase

from core_logic.entities.report import (
    ReportCourseRef,
    ReportGroupRef,
    ReportMarkFact,
    ReportStudentRef,
    ReportWorkRef,
    StudentPerformanceItemSource,
    StudentPerformanceParticipationFact,
    StudentPerformanceSource,
    WorkAnalysisItemSource,
    WorkAnalysisSource,
)
from core_logic.services.report_summary_service import ReportSummaryService


class ReportSummaryServiceTests(TestCase):
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

        report = ReportSummaryService().build_student_performance(source)

        stat = report.students_stats[0]
        self.assertEqual(stat['total_participations'], 2)
        self.assertEqual(stat['completed_participations'], 1)
        self.assertEqual(stat['completion_rate'], 50)
        self.assertEqual(stat['average_score'], 4.5)
        self.assertEqual(stat['average_pct'], 75)
        self.assertEqual(stat['last_activity'], latest)
        self.assertEqual(report.summary_stats, {
            'total_students': 1,
            'high_performers': 0,
            'need_attention': 0,
            'avg_completion_rate': 50,
            'avg_pct': 75,
        })

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

        report = ReportSummaryService().build_student_performance(source)

        self.assertIsNone(report.students_stats[0]['average_pct'])
        self.assertEqual(report.summary_stats['avg_pct'], 0)

    def test_builds_work_analysis_from_mark_facts(self):
        source = WorkAnalysisSource(
            works=[
                WorkAnalysisItemSource(
                    work=self._work('work-1', 'Контрольная'),
                    events_count=2,
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

        report = ReportSummaryService().build_work_analysis(source)

        first = report.works_analysis[0]
        self.assertEqual(first['events_count'], 2)
        self.assertEqual(first['total_marks'], 2)
        self.assertEqual(first['average_score'], 4.5)
        self.assertEqual(first['average_percentage'], 80)
        self.assertEqual(first['difficulty_assessment'], 'Средняя')
        self.assertEqual(first['score_distribution'], [
            {'score': 4, 'count': 1},
            {'score': 5, 'count': 1},
        ])
        self.assertEqual(report.works_analysis[1]['difficulty_assessment'], 'Очень сложная')
        self.assertEqual(report.summary_stats['total_works'], 2)
        self.assertEqual(report.summary_stats['total_marks'], 3)
        self.assertEqual(report.summary_stats['hard_works'], 1)
        self.assertEqual(report.summary_stats['avg_score'], 3.25)

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

        report = ReportSummaryService().build_work_analysis(source)

        work = report.works_analysis[0]
        self.assertEqual(work['average_score'], 0)
        self.assertEqual(work['average_percentage'], 0)
        self.assertEqual(work['score_distribution'], [])
        self.assertEqual(work['difficulty_assessment'], 'Очень сложная')

    @staticmethod
    def _work(pk, name):
        return ReportWorkRef(
            pk=pk,
            name=name,
            work_type='control',
            work_type_display='Контрольная работа',
            duration=45,
        )
