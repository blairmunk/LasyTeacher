"""Build task export payload."""

from dataclasses import dataclass

from core_logic.entities.task import TaskExportData, TaskExportFilters
from core_logic.interfaces.task_export_repo import ITaskExportRepository
from core_logic.services.task_export_service import TaskExportService


@dataclass(frozen=True)
class ExportTasksRequest:
    filters: TaskExportFilters
    export_date: str
    include_groups: bool = True
    include_topics: bool = True


class ExportTasksUseCase:
    def __init__(
        self,
        task_export_repo: ITaskExportRepository,
        export_service: TaskExportService | None = None,
    ):
        self.task_export_repo = task_export_repo
        self.export_service = export_service or TaskExportService()

    def execute(self, request: ExportTasksRequest) -> TaskExportData:
        return TaskExportData(
            payload=self.export_service.build(
                self.task_export_repo.get_task_export_sources(request.filters),
                export_date=request.export_date,
                include_groups=request.include_groups,
                include_topics=request.include_topics,
            ),
        )
