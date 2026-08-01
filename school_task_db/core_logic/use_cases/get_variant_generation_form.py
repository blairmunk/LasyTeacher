"""Build data for the work variant generation form."""

from core_logic.entities.work import VariantGenerationFormData
from core_logic.interfaces.work_variant_generation_repo import (
    IWorkVariantGenerationRepository,
)
from core_logic.services.work_variant_composition_service import (
    WorkVariantCompositionService,
)


class GetVariantGenerationFormUseCase:
    def __init__(
        self,
        work_repo: IWorkVariantGenerationRepository,
        composition_service: WorkVariantCompositionService | None = None,
    ):
        self.work_repo = work_repo
        self.composition_service = (
            composition_service or WorkVariantCompositionService()
        )

    def execute(self, work_id: str) -> VariantGenerationFormData:
        work = self.work_repo.get_work_generation_target(str(work_id))
        if not work:
            return VariantGenerationFormData(work=None, status='not_found')
        return VariantGenerationFormData(
            work=work,
            work_groups=self.composition_service.build_generation_groups(
                self.work_repo.get_variant_generation_group_sources(
                    str(work_id),
                ),
            ),
        )
