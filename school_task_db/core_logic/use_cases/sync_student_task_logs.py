"""Synchronize the student learning-history projection from a mark."""

from core_logic.interfaces.student_repo import IStudentRepository


class SyncStudentTaskLogsUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(self, mark_id: str) -> int:
        if not mark_id:
            return 0
        return self.student_repo.sync_student_task_logs(mark_id)

