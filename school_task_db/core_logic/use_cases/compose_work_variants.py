"""Compose variants for a work."""

from dataclasses import dataclass

from core_logic.entities.work import ComposeWorkVariantsResult
from core_logic.interfaces.work_variant_generation_repo import (
    IWorkVariantGenerationRepository,
)
from core_logic.services.work_variant_composition_service import (
    WorkVariantCompositionService,
)


MAX_COMPOSITION_ATTEMPTS = 3


@dataclass(frozen=True)
class ComposeWorkVariantsRequest:
    work_id: str
    count: int


class ComposeWorkVariantsUseCase:
    def __init__(
        self,
        work_repo: IWorkVariantGenerationRepository,
        composition_service=None,
    ):
        self.work_repo = work_repo
        self.composition_service = (
            composition_service or WorkVariantCompositionService()
        )

    def execute(
        self,
        request: ComposeWorkVariantsRequest,
    ) -> ComposeWorkVariantsResult:
        for _attempt in range(MAX_COMPOSITION_ATTEMPTS):
            composition_input = (
                self.work_repo.get_variant_composition_input(
                    request.work_id,
                )
            )
            if composition_input is None:
                return ComposeWorkVariantsResult(
                    created_count=0,
                    status='not_found',
                )

            plan = self.composition_service.compose(
                composition_input,
                count=request.count,
            )
            save_result = self.work_repo.save_variant_composition_plan(
                work_id=request.work_id,
                expected_variant_counter=composition_input.variant_counter,
                plan=plan,
            )
            if save_result.status == 'saved':
                return ComposeWorkVariantsResult(
                    created_count=len(plan.variants),
                )
            if save_result.status == 'not_found':
                return ComposeWorkVariantsResult(
                    created_count=0,
                    status='not_found',
                )
            if save_result.status != 'conflict':
                raise ValueError(
                    'Unsupported variant composition save status: '
                    f'{save_result.status}',
                )

        return ComposeWorkVariantsResult(
            created_count=0,
            status='conflict',
        )
