"""Build work detail page data."""

from core_logic.entities.work import (
    WorkDetailData,
    WorkDetailSpecPreviewItem,
)
from core_logic.interfaces.presentation_profile_catalog_repo import (
    IPresentationProfileCatalogRepository,
)
from core_logic.interfaces.work_read_repo import IWorkReadRepository
from core_logic.services.work_service import WorkService
from core_logic.services.work_score_allocation_service import (
    WorkScoreAllocationService,
    WorkScoreSpecRow,
)
from core_logic.services.work_variant_composition_service import (
    WorkVariantCompositionService,
)
from core_logic.value_objects.document_recipes import (
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
)
from core_logic.value_objects.work_content_plan import (
    build_work_content_plan,
)


class GetWorkDetailUseCase:
    def __init__(
        self,
        work_read_repo: IWorkReadRepository,
        work_service: WorkService,
        presentation_profile_repo: (
            IPresentationProfileCatalogRepository | None
        ) = None,
        score_allocation_service=None,
        composition_service=None,
    ):
        self.work_read_repo = work_read_repo
        self.work_service = work_service
        self.presentation_profile_repo = presentation_profile_repo
        self.score_allocation_service = (
            score_allocation_service or WorkScoreAllocationService()
        )
        self.composition_service = (
            composition_service or WorkVariantCompositionService()
        )

    def execute(self, work_id: str) -> WorkDetailData:
        work = self.work_read_repo.get_work_detail(work_id)
        if work is None:
            return WorkDetailData()

        variants = self.work_read_repo.get_detail_variants(work_id)
        analog_groups = self.composition_service.build_work_detail_groups(
            self.work_read_repo.get_detail_analog_groups(work_id),
        )
        content_blocks = self.work_read_repo.get_detail_content_blocks(work_id)
        score_spec_rows = tuple(
            WorkScoreSpecRow(
                spec_row_id=(
                    group.selection_id or group.analog_group.pk
                ),
                count=group.count,
                weight=group.weight,
                is_assessable=group.is_assessable,
            )
            for group in analog_groups
        )
        spec_preview = self._build_spec_preview(
            max_score=work.max_score,
            analog_groups=analog_groups,
            score_spec_rows=score_spec_rows,
        )

        return WorkDetailData(
            work=work,
            effective_max_score=(
                self.score_allocation_service.effective_max_score(
                    max_score=work.max_score,
                    spec_rows=score_spec_rows,
                )
            ),
            variants=variants,
            analog_groups=analog_groups,
            spec_preview=spec_preview,
            content_plan=build_work_content_plan(
                task_rows=analog_groups,
                content_rows=content_blocks,
            ),
            work_presentation_profiles=self._presentation_profiles(
                WORK_DOCUMENT_TYPE,
            ),
            remedial_sheet_presentation_profiles=self._presentation_profiles(
                REMEDIAL_SHEET_DOCUMENT_TYPE,
            ),
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

    def _presentation_profiles(self, document_type: str):
        if self.presentation_profile_repo is None:
            return []
        return self.presentation_profile_repo.list_presentation_profiles(
            document_type,
        )

    def _build_spec_preview(
        self,
        max_score,
        analog_groups,
        score_spec_rows,
    ):
        groups_by_id = {
            (group.selection_id or group.analog_group.pk): group
            for group in analog_groups
        }
        preview_by_group_id = {}
        for allocation in self.score_allocation_service.allocate(
            max_score=max_score,
            spec_rows=score_spec_rows,
        ):
            preview = preview_by_group_id.setdefault(
                allocation.spec_row_id,
                {
                    'per_task': allocation.points,
                    'total_points': 0,
                },
            )
            preview['per_task'] = allocation.points
            preview['total_points'] += allocation.points

        return [
            WorkDetailSpecPreviewItem(
                wg=groups_by_id[group_id],
                per_task=preview['per_task'],
                total_points=preview['total_points'],
                available_count=groups_by_id[group_id].available_count,
            )
            for group_id, preview in preview_by_group_id.items()
        ]
