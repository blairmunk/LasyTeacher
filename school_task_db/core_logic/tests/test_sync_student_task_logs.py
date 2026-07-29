from unittest import TestCase

from core_logic.use_cases.sync_student_task_logs import (
    SyncStudentTaskLogsUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.synced_mark_ids = []

    def sync_student_task_logs(self, mark_id):
        self.synced_mark_ids.append(mark_id)
        return 2


class SyncStudentTaskLogsUseCaseTests(TestCase):
    def test_delegates_projection_sync_by_mark_id(self):
        repo = FakeStudentRepository()

        created_count = SyncStudentTaskLogsUseCase(repo).execute('mark-1')

        self.assertEqual(created_count, 2)
        self.assertEqual(repo.synced_mark_ids, ['mark-1'])

    def test_empty_mark_id_is_ignored(self):
        repo = FakeStudentRepository()

        created_count = SyncStudentTaskLogsUseCase(repo).execute('')

        self.assertEqual(created_count, 0)
        self.assertEqual(repo.synced_mark_ids, [])

