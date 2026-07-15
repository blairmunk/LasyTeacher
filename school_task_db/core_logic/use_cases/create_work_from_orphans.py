"""Create a work from selected orphan variants."""

from dataclasses import dataclass
from typing import List

from core_logic.entities.work import CreateWorkFromOrphansResult
from core_logic.interfaces.work_repo import (
    AttachVariantsToWorkParams,
    CreateWorkParams,
    IWorkRepository,
)


DEFAULT_ORPHAN_WORK_NAME = 'Работа над ошибками'


@dataclass(frozen=True)
class CreateWorkFromOrphansRequest:
    variant_ids: List[str]
    work_name: str = DEFAULT_ORPHAN_WORK_NAME


class CreateWorkFromOrphansUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(
        self,
        request: CreateWorkFromOrphansRequest,
    ) -> CreateWorkFromOrphansResult:
        if not request.variant_ids:
            return CreateWorkFromOrphansResult(status='empty_selection')

        variants = self.work_repo.get_orphan_variant_refs(request.variant_ids)
        if not variants:
            return CreateWorkFromOrphansResult(status='not_found')

        work_name = request.work_name.strip() or DEFAULT_ORPHAN_WORK_NAME
        max_score = max(variant.total_max_points for variant in variants)
        work_id = self.work_repo.create_work(
            CreateWorkParams(
                name=work_name,
                work_type=self._detect_work_type(
                    [variant.variant_type for variant in variants],
                ),
                max_score=max_score,
                variant_counter=len(variants),
            )
        )
        attached_count = self.work_repo.attach_variants_to_work(
            AttachVariantsToWorkParams(
                work_id=work_id,
                variant_ids=[variant.pk for variant in variants],
                work_name_snapshot=work_name,
                max_score_snapshot=max_score,
            )
        )

        return CreateWorkFromOrphansResult(
            status='created',
            work_id=work_id,
            work_name=work_name,
            variant_count=attached_count,
        )

    def _detect_work_type(self, variant_types: List[str]) -> str:
        if 'remedial' in variant_types:
            return 'remedial'
        if 'individual' in variant_types:
            return 'individual'
        return 'test'
