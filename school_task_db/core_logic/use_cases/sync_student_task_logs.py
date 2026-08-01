"""Synchronize the student learning-history projection from a mark."""

from core_logic.interfaces.student_repo import IStudentRepository
from core_logic.services.student_task_log_sync_service import (
    StudentTaskLogSyncService,
)


class SyncStudentTaskLogsUseCase:
    def __init__(
        self,
        student_repo: IStudentRepository,
        service: StudentTaskLogSyncService | None = None,
    ):
        self.student_repo = student_repo
        self.service = service or StudentTaskLogSyncService()

    def execute(self, mark_id: str) -> int:
        if not mark_id:
            return 0
        source = self.student_repo.get_task_log_sync_source(mark_id)
        if source is None:
            return 0
        return self.student_repo.apply_task_log_sync(
            self.service.build(source),
        )
