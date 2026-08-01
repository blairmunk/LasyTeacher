from datetime import datetime
from unittest import TestCase

from core_logic.entities.student import (
    TaskLogSyncSource,
    TaskLogSyncTask,
    TaskLogSyncVariantTask,
)
from core_logic.services.student_task_log_sync_service import (
    StudentTaskLogSyncService,
)
from core_logic.use_cases.sync_student_task_logs import (
    SyncStudentTaskLogsUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.source_requests = []
        self.applied_plans = []
        self.source = TaskLogSyncSource(
            mark_id='mark-1',
            student_id='student-1',
            event_id='event-1',
            variant_id=None,
            completed_at=datetime(2026, 8, 1),
            task_scores={
                'task-1': {'points': 2, 'max_points': 2},
            },
            tasks=(TaskLogSyncTask(task_id='task-1'),),
        )

    def get_task_log_sync_source(self, mark_id):
        self.source_requests.append(mark_id)
        return self.source

    def apply_task_log_sync(self, plan):
        self.applied_plans.append(plan)
        return 2


class SyncStudentTaskLogsUseCaseTests(TestCase):
    def test_builds_and_applies_projection_by_mark_id(self):
        repo = FakeStudentRepository()

        created_count = SyncStudentTaskLogsUseCase(repo).execute('mark-1')

        self.assertEqual(created_count, 2)
        self.assertEqual(repo.source_requests, ['mark-1'])
        self.assertEqual(len(repo.applied_plans), 1)
        entry = repo.applied_plans[0].entries[0]
        self.assertEqual(entry.task_id, 'task-1')
        self.assertEqual(entry.percentage, 100.0)
        self.assertTrue(entry.is_correct)

    def test_empty_mark_id_is_ignored(self):
        repo = FakeStudentRepository()

        created_count = SyncStudentTaskLogsUseCase(repo).execute('')

        self.assertEqual(created_count, 0)
        self.assertEqual(repo.source_requests, [])
        self.assertEqual(repo.applied_plans, [])

    def test_missing_mark_is_ignored(self):
        repo = FakeStudentRepository()
        repo.source = None

        created_count = SyncStudentTaskLogsUseCase(repo).execute('missing')

        self.assertEqual(created_count, 0)
        self.assertEqual(repo.applied_plans, [])


class StudentTaskLogSyncServiceTests(TestCase):
    def test_resolves_repeated_tasks_by_variant_task_identity(self):
        source = TaskLogSyncSource(
            mark_id='mark-1',
            student_id='student-1',
            event_id='event-1',
            variant_id='variant-1',
            completed_at=datetime(2026, 8, 1),
            task_scores={
                'slot-1': {
                    'task_id': 'task-1',
                    'points': 0,
                    'max_points': 2,
                },
                'slot-2': {
                    'task_id': 'task-1',
                    'points': 2,
                    'max_points': 2,
                },
            },
            variant_tasks=(
                TaskLogSyncVariantTask('slot-1', 'task-1'),
                TaskLogSyncVariantTask('slot-2', 'task-1'),
            ),
            tasks=(TaskLogSyncTask(task_id='task-1'),),
        )

        plan = StudentTaskLogSyncService().build(source)

        self.assertEqual(len(plan.entries), 2)
        self.assertEqual(
            [entry.variant_task_id for entry in plan.entries],
            ['slot-1', 'slot-2'],
        )
        self.assertEqual(
            [entry.is_correct for entry in plan.entries],
            [False, True],
        )

    def test_builds_denormalized_task_metadata(self):
        source = TaskLogSyncSource(
            mark_id='mark-1',
            student_id='student-1',
            event_id='event-1',
            variant_id=None,
            completed_at=datetime(2026, 8, 1),
            task_scores={
                'task-1': {
                    'points': 1,
                    'max_points': 4,
                    'comment': 'Повторить формулу',
                },
            },
            tasks=(
                TaskLogSyncTask(
                    task_id='task-1',
                    topic_id='topic-1',
                    subtopic_id='subtopic-1',
                    analog_group_id='group-1',
                    difficulty=3,
                ),
            ),
        )

        entry = StudentTaskLogSyncService().build(source).entries[0]

        self.assertEqual(entry.topic_id, 'topic-1')
        self.assertEqual(entry.subtopic_id, 'subtopic-1')
        self.assertEqual(entry.analog_group_id, 'group-1')
        self.assertEqual(entry.comment, 'Повторить формулу')
        self.assertEqual(entry.percentage, 25.0)
        self.assertFalse(entry.is_correct)
