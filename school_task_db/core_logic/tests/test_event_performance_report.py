import datetime as dt
from unittest import TestCase

from core_logic.entities.event_performance_report import (
    EventReportCapturedEventFact,
    EventReportCapturedTaskFact,
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
from core_logic.services.event_report_task_fact_service import (
    EventReportTaskFactService,
)
from core_logic.services.event_report_source_service import (
    resolve_event_report_assessment_mode,
    resolve_event_report_event_ref,
)
from core_logic.value_objects.work_assessment import (
    WORK_ASSESSMENT_MODE_AGGREGATE,
    WORK_ASSESSMENT_MODE_VARIANT,
)
from core_logic.value_objects.attempt_status import (
    resolve_historical_participation_status,
)
from core_logic.value_objects.report_task_slot import report_task_slot_key
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
                    group_key='spec-1',
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

    def test_task_slot_key_prefers_specification_identity(self):
        self.assertEqual(
            report_task_slot_key(
                source_selection_id='selection-1',
                content_order=30,
                position=7,
                occurrence=2,
            ),
            'selection:selection-1:slot:2',
        )
        self.assertEqual(
            report_task_slot_key(
                content_order=30,
                position=7,
                occurrence=2,
            ),
            'content:30:slot:2',
        )
        self.assertEqual(
            report_task_slot_key(position=7),
            'position:7',
        )

    def test_builds_stable_task_slots_from_captured_facts(self):
        captured = (
            self._captured_task('s1', order=1, points=0),
            self._captured_task('s1', order=2, points=1),
            self._captured_task('s2', order=1, points=2),
            self._captured_task('s2', order=2, points=2),
            self._captured_task(
                's1',
                order=3,
                points=0,
                is_assessable=False,
            ),
        )

        facts = EventReportTaskFactService().build(captured)

        self.assertEqual(
            [fact.group_key for fact in facts.task_scores],
            [
                'selection:selection-1:slot:1',
                'selection:selection-1:slot:2',
                'selection:selection-1:slot:1',
                'selection:selection-1:slot:2',
            ],
        )
        self.assertEqual(len(facts.specification), 2)
        self.assertEqual(
            [fact.order for fact in facts.specification],
            [1, 2],
        )
        self.assertEqual(
            facts.specification[0].codifier_requirements,
            ('ОГЭ: 2.1',),
        )

    def test_report_assessment_mode_prefers_consistent_snapshot(self):
        self.assertEqual(
            resolve_event_report_assessment_mode(
                (WORK_ASSESSMENT_MODE_AGGREGATE,) * 2,
                fallback_mode=WORK_ASSESSMENT_MODE_VARIANT,
            ),
            WORK_ASSESSMENT_MODE_AGGREGATE,
        )
        self.assertEqual(
            resolve_event_report_assessment_mode(
                (
                    WORK_ASSESSMENT_MODE_AGGREGATE,
                    WORK_ASSESSMENT_MODE_VARIANT,
                ),
                fallback_mode=WORK_ASSESSMENT_MODE_VARIANT,
            ),
            WORK_ASSESSMENT_MODE_VARIANT,
        )

    def test_report_event_ref_prefers_consistent_historical_metadata(self):
        captured_date = dt.datetime(2026, 7, 1)
        captured = (
            EventReportCapturedEventFact(
                name='Исходное событие',
                planned_date=captured_date,
                work_name='Исходная работа',
                work_assessment_mode=WORK_ASSESSMENT_MODE_AGGREGATE,
            ),
        )

        result = resolve_event_report_event_ref(self.source.event, captured)

        self.assertEqual(result.name, 'Исходное событие')
        self.assertEqual(result.planned_date, captured_date)
        self.assertEqual(result.work_name, 'Исходная работа')
        self.assertEqual(
            result.work_assessment_mode,
            WORK_ASSESSMENT_MODE_AGGREGATE,
        )
        self.assertEqual(result.status, self.source.event.status)
        self.assertEqual(result.course_name, self.source.event.course_name)

    def test_report_event_ref_uses_current_value_for_conflicting_snapshots(self):
        captured = tuple(
            EventReportCapturedEventFact(
                name=name,
                planned_date=self.source.event.planned_date,
                work_name='Исходная работа',
            )
            for name in ('Первое название', 'Второе название')
        )

        result = resolve_event_report_event_ref(self.source.event, captured)

        self.assertEqual(result.name, self.source.event.name)
        self.assertEqual(result.work_name, 'Исходная работа')

    def test_captured_attempt_has_stable_graded_status(self):
        self.assertEqual(
            resolve_historical_participation_status(
                'absent',
                has_attempt=True,
            ),
            'graded',
        )
        self.assertEqual(
            resolve_historical_participation_status(
                'absent',
                has_attempt=False,
            ),
            'absent',
        )

    @staticmethod
    def _captured_task(
        student_id,
        order,
        points,
        is_assessable=True,
    ):
        return EventReportCapturedTaskFact(
            student_id=student_id,
            student_name=student_id,
            order=order,
            topic_name='Динамика',
            subtopic_name=f'Задание {order}',
            source_selection_id='selection-1',
            content_order=10,
            is_assessable=is_assessable,
            points=points,
            max_points=2,
            content_element='1.2',
            requirement_element='2.1',
            codifier_requirements=('ОГЭ: 2.1',),
        )
