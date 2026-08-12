"""Plan or apply legacy task classification links."""

from core_logic.entities.task_classification_backfill import (
    BackfillTaskClassificationsResult,
)
from core_logic.services.task_classification_backfill_planner import (
    plan_task_classification_backfill,
)


class BackfillTaskClassificationsUseCase:
    def __init__(self, backfill_repo, transaction_manager):
        self.backfill_repo = backfill_repo
        self.transaction_manager = transaction_manager

    def execute(self, request):
        with self.transaction_manager.atomic():
            plan = plan_task_classification_backfill(
                self.backfill_repo.get_backfill_snapshot(),
            )
            if request.apply:
                self.backfill_repo.apply_backfill_plan(plan)
        return BackfillTaskClassificationsResult(
            status='applied' if request.apply else 'preview',
            plan=plan,
        )
