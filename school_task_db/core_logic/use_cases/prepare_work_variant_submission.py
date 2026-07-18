"""Prepare work/variant action POST data."""

from dataclasses import dataclass
from typing import Mapping, Sequence

from core_logic.use_cases.bulk_delete_variants import BulkDeleteVariantsRequest
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansRequest,
)
from core_logic.use_cases.delete_variant import DeleteVariantRequest


@dataclass(frozen=True)
class PrepareVariantActionSubmissionRequest:
    data: Mapping[str, Sequence[str]]
    variant_id: str = ''
    work_id: str = ''


class PrepareDeleteVariantSubmissionUseCase:
    def execute(
        self,
        request: PrepareVariantActionSubmissionRequest,
    ) -> DeleteVariantRequest:
        return DeleteVariantRequest(
            variant_id=request.variant_id,
            action=_first(request.data, 'action', 'delete'),
        )


class PrepareBulkDeleteVariantsSubmissionUseCase:
    def execute(
        self,
        request: PrepareVariantActionSubmissionRequest,
    ) -> BulkDeleteVariantsRequest:
        return BulkDeleteVariantsRequest(
            work_id=request.work_id,
            variant_ids=_list(request.data, 'variant_ids'),
        )


class PrepareCreateWorkFromOrphansSubmissionUseCase:
    def execute(
        self,
        request: PrepareVariantActionSubmissionRequest,
    ) -> CreateWorkFromOrphansRequest:
        return CreateWorkFromOrphansRequest(
            variant_ids=_list(request.data, 'variant_ids'),
            work_name=_first(request.data, 'work_name'),
        )


def _first(
    data: Mapping[str, Sequence[str]],
    key: str,
    default: str = '',
) -> str:
    values = data.get(key)
    if not values:
        return default
    return str(values[0])


def _list(data: Mapping[str, Sequence[str]], key: str):
    values = data.get(key)
    if not values:
        return []
    return [str(value) for value in values]
