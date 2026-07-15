"""Build current placeholder response for single variant generation."""

from core_logic.entities.work import VariantGenerationPlaceholderResult
from core_logic.interfaces.work_repo import IWorkRepository


class GetVariantGenerationPlaceholderUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self, variant_id: str) -> VariantGenerationPlaceholderResult:
        variant_info = self.work_repo.get_variant_generation_info(variant_id)
        if not variant_info:
            return VariantGenerationPlaceholderResult(status='not_found')

        return VariantGenerationPlaceholderResult(
            status='ready',
            message=(
                f'Вариант {variant_info.number} работы '
                f'"{variant_info.work_name}" будет добавлен в следующей версии'
            ),
        )
