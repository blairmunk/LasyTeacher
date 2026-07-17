"""Build work detail page data."""

from core_logic.entities.work import WorkDetailData
from core_logic.interfaces.work_repo import IWorkRepository
from core_logic.services.work_service import WorkService


class GetWorkDetailUseCase:
    def __init__(
        self,
        work_repo: IWorkRepository,
        work_service: WorkService,
    ):
        self.work_repo = work_repo
        self.work_service = work_service

    def execute(self, work_id: str) -> WorkDetailData:
        work = self.work_repo.get_work_detail(work_id)
        if work is None:
            return WorkDetailData()

        variants = self.work_repo.get_detail_variants(work_id)
        analog_groups = self.work_repo.get_detail_analog_groups(work_id)
        spec_preview = self.work_repo.get_spec_preview(work_id)

        return WorkDetailData(
            work=work,
            variants=variants,
            analog_groups=analog_groups,
            spec_preview=spec_preview,
            show_sync_button=self.work_service.should_show_sync_button(
                has_variants=self._has_items(variants),
                has_analog_groups=self._has_items(analog_groups),
            ),
        )

    @staticmethod
    def _has_items(items) -> bool:
        if hasattr(items, 'exists'):
            return items.exists()
        return bool(items)
