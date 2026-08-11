"""Build dashboard summary data for the index page."""

from core_logic.entities.core import DashboardSummaryData
from core_logic.interfaces.dashboard_summary_repo import (
    IDashboardSummaryRepository,
)


class GetDashboardSummaryUseCase:
    def __init__(self, core_repo: IDashboardSummaryRepository):
        self.core_repo = core_repo

    def execute(self) -> DashboardSummaryData:
        return DashboardSummaryData(
            tasks_count=self.core_repo.count_tasks(),
            works_count=self.core_repo.count_works(),
            variants_count=self.core_repo.count_variants(),
            orphan_variants_count=self.core_repo.count_orphan_variants(),
            students_count=self.core_repo.count_students(),
            events_count=self.core_repo.count_events(),
            groups_count=self.core_repo.count_analog_groups(),
        )
