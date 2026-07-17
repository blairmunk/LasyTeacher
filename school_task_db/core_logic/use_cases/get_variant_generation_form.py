"""Build data for the work variant generation form."""

from core_logic.entities.work import VariantGenerationFormData
from core_logic.interfaces.work_repo import IWorkRepository


class GetVariantGenerationFormUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self, work_id: str) -> VariantGenerationFormData:
        work = self.work_repo.get_work_generation_target(str(work_id))
        if not work:
            return VariantGenerationFormData(work=None, status='not_found')
        return VariantGenerationFormData(work=work)
