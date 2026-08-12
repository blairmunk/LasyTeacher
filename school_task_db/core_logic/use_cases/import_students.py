"""Plan and optionally apply a student CSV import."""

from core_logic.entities.student_import import (
    ImportStudentsRequest,
    ImportStudentsResult,
    StudentImportPlan,
)
from core_logic.interfaces.student_import_command_repo import (
    IStudentImportCommandRepository,
)
from core_logic.interfaces.student_import_snapshot_repo import (
    IStudentImportSnapshotRepository,
)
from core_logic.interfaces.transaction_manager import ITransactionManager
from core_logic.services.student_import_planner import StudentImportPlanner


class ImportStudentsUseCase:
    def __init__(
        self,
        snapshot_repo: IStudentImportSnapshotRepository,
        command_repo: IStudentImportCommandRepository,
        transaction_manager: ITransactionManager,
        planner: StudentImportPlanner | None = None,
    ):
        self.snapshot_repo = snapshot_repo
        self.command_repo = command_repo
        self.transaction_manager = transaction_manager
        self.planner = planner or StudentImportPlanner()

    def execute(self, request: ImportStudentsRequest) -> ImportStudentsResult:
        if request.dry_run:
            plan = self._build_plan(request)
        else:
            with self.transaction_manager.atomic():
                plan = self._build_plan(request)
                self.command_repo.apply_student_import_plan(plan)
        return ImportStudentsResult(
            status='planned' if request.dry_run else 'imported',
            dry_run=request.dry_run,
            stats=plan.stats,
        )

    def _build_plan(self, request: ImportStudentsRequest) -> StudentImportPlan:
        return self.planner.build(
            request.rows,
            self.snapshot_repo.get_student_import_snapshot(),
        )
