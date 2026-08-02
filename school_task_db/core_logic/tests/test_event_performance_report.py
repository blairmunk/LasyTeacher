import datetime as dt
from unittest import TestCase

from core_logic.entities.event_performance_report import (
    EventPerformanceReportSource,
    EventReportEventRef,
    EventReportNarrative,
    EventReportParticipantFact,
    EventReportSpecificationFact,
    EventReportTaskScoreFact,
    SaveEventReportNarrativeParams,
    SaveEventReportNarrativeResult,
)
from core_logic.services.event_performance_report_service import (
    EventPerformanceReportService,
)
from core_logic.use_cases.get_event_performance_report import (
    GetEventPerformanceReportUseCase,
)
from core_logic.use_cases.save_event_report_narrative import (
    SaveEventReportNarrativeUseCase,
)


class FakeEventReportRepository:
    def __init__(self, source):
        self.source = source
        self.saved = None

    def get_event_report_source(self, event_id):
        return self.source if event_id == self.source.event.pk else None

    def save_event_report_narrative(self, params):
        self.saved = params
        return SaveEventReportNarrativeResult(
            status='saved',
            event_id=params.event_id,
        )


class EventPerformanceReportTests(TestCase):
    def setUp(self):
        self.source = EventPerformanceReportSource(
            event=EventReportEventRef(
                pk='event-1',
                name='Контрольная по механике',
                status='graded',
                status_display='Проверено',
                planned_date=dt.datetime(2026, 7, 15),
                work_name='Контрольная',
                course_name='Физика 9',
            ),
            participants=(
                EventReportParticipantFact(
                    student_id='s1',
                    student_name='Иванов Иван',
                    status='graded',
                    score=2,
                    points=2,
                    max_points=5,
                    mistakes_analysis='Не записана формула',
                    teacher_comment='Нужна индивидуальная консультация',
                    needs_attention=True,
                ),
                EventReportParticipantFact(
                    student_id='s2',
                    student_name='Петрова Мария',
                    status='graded',
                    score=5,
                    points=5,
                    max_points=5,
                ),
                EventReportParticipantFact(
                    student_id='s3',
                    student_name='Сидоров Пётр',
                    status='absent',
                ),
            ),
            task_scores=(
                self._task_score('s1', 'Иванов Иван', points=0),
                self._task_score('s2', 'Петрова Мария', points=2),
            ),
            specification=(
                EventReportSpecificationFact(
                    order=1,
                    topic_name='Динамика',
                    subtopic_name='Второй закон Ньютона',
                    content_element='1.2',
                    content_element_descriptions=(
                        'ОГЭ 2026: Второй закон Ньютона',
                    ),
                    codifier_requirements=('ОГЭ 2026: 2.1',),
                ),
            ),
            narrative=EventReportNarrative(planned_actions='Консультация'),
        )

    @staticmethod
    def _task_score(student_id, student_name, points):
        return EventReportTaskScoreFact(
            group_key='spec-1',
            order=1,
            topic_name='Динамика',
            subtopic_name='Второй закон Ньютона',
            student_id=student_id,
            student_name=student_name,
            points=points,
            max_points=2,
            comment='Не записана формула' if points == 0 else '',
        )

    def test_builds_event_report_statistics_and_weak_topics(self):
        report = EventPerformanceReportService().build(self.source)

        self.assertEqual(report.participants_total, 3)
        self.assertEqual(report.present_count, 2)
        self.assertEqual(report.absent_count, 1)
        self.assertEqual(report.average_score, 3.5)
        self.assertEqual(report.pass_percentage, 50)
        self.assertEqual(report.quality_percentage, 50)
        self.assertEqual(report.task_summaries[0].error_percentage, 50)
        self.assertEqual(report.specification_items[0].order, 1)
        self.assertEqual(
            report.specification_items[0].requirement_elements,
            ('ОГЭ 2026: 2.1',),
        )
        self.assertEqual(
            report.specification_items[0].content_element_descriptions,
            ('ОГЭ 2026: Второй закон Ньютона',),
        )
        self.assertEqual(report.teacher_notes[0].student_name, 'Иванов Иван')
        self.assertTrue(report.teacher_notes[0].needs_attention)
        self.assertEqual(
            report.task_summaries[0].failed_students,
            ('Иванов Иван',),
        )
        self.assertEqual(
            report.weak_topics[0].label,
            'Динамика: Второй закон Ньютона',
        )
        self.assertIn('Не записана формула', report.common_errors)
        self.assertTrue(report.suggested_actions)

    def test_use_cases_delegate_read_and_narrative_save(self):
        repo = FakeEventReportRepository(self.source)
        report = GetEventPerformanceReportUseCase(repo).execute('event-1')
        params = SaveEventReportNarrativeParams(
            event_id='event-1',
            narrative=EventReportNarrative(recommendations='Повторить тему'),
        )
        save_result = SaveEventReportNarrativeUseCase(repo).execute(params)

        self.assertEqual(report.event.name, self.source.event.name)
        self.assertEqual(save_result.status, 'saved')
        self.assertEqual(repo.saved, params)

    def test_missing_event_returns_none(self):
        repo = FakeEventReportRepository(self.source)

        self.assertIsNone(
            GetEventPerformanceReportUseCase(repo).execute('missing'),
        )
