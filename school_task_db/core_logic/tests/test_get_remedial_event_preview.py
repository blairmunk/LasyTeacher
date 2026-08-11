from unittest import TestCase

from core_logic.entities.event import (
    EventEntity,
    ParticipationAttemptData,
    StudentSummary,
    VariantSummary,
)
from core_logic.use_cases.get_remedial_event_preview import (
    GetRemedialEventPreviewUseCase,
)


class FakeEventRepository:
    def get_by_id(self, event_id):
        if event_id == 'missing':
            return None
        return EventEntity(
            id=event_id,
            name='КР',
            work_id='work-1',
            work_name='Контрольная',
            status='graded',
        )

    def get_participation_attempts(self, event_id):
        return [
            ParticipationAttemptData(
                student=StudentSummary(id='s1', full_name='Иванов Иван'),
                variant=VariantSummary(id='v1', number=1),
                score=2,
                points=5,
                max_points=7,
                task_scores={
                    't1': {'points': 0, 'max_points': 2},
                    'variant-task-2': {
                        'task_id': 't2',
                        'points': 5,
                        'max_points': 5,
                    },
                },
            ),
            ParticipationAttemptData(
                student=StudentSummary(id='s2', full_name='Петров Пётр'),
                variant=None,
            ),
        ]


class GetRemedialEventPreviewUseCaseTests(TestCase):
    def test_execute_builds_preview_rows_and_counts_weak_students(self):
        result = GetRemedialEventPreviewUseCase(
            event_repo=FakeEventRepository(),
            event_attempt_repo=FakeEventRepository(),
        ).execute('event-1')

        self.assertTrue(result.success)
        self.assertEqual(result.event.name, 'КР')
        self.assertEqual(result.work.name, 'Контрольная')
        self.assertEqual(result.weak_students, 1)
        self.assertEqual(len(result.analysis), 2)

        weak_row = result.analysis[0]
        self.assertEqual(weak_row['student'].get_full_name(), 'Иванов Иван')
        self.assertEqual(weak_row['score_pct'], 71.4)
        self.assertEqual(weak_row['weak_tasks'], ['t1'])
        self.assertEqual(weak_row['weak_tasks_count'], 1)
        self.assertEqual(weak_row['status'], 'weak')

        unchecked_row = result.analysis[1]
        self.assertIsNone(unchecked_row['score_pct'])
        self.assertEqual(unchecked_row['status'], 'Не проверено')

    def test_execute_returns_failure_for_missing_event(self):
        result = GetRemedialEventPreviewUseCase(
            event_repo=FakeEventRepository(),
            event_attempt_repo=FakeEventRepository(),
        ).execute('missing')

        self.assertFalse(result.success)
        self.assertEqual(result.message, 'Событие не найдено.')

    def test_execute_rejects_event_before_review(self):
        repo = FakeEventRepository()
        event = repo.get_by_id('event-1')
        repo.get_by_id = lambda event_id: EventEntity(
            id=event.id,
            name=event.name,
            work_id=event.work_id,
            work_name=event.work_name,
            status='completed',
        )

        result = GetRemedialEventPreviewUseCase(
            event_repo=repo,
            event_attempt_repo=repo,
        ).execute('event-1')

        self.assertFalse(result.success)
        self.assertIn('после начала проверки', result.message)
