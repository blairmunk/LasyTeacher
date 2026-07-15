"""Build data for rendering a remedial sheet."""

from core_logic.entities.work import RemedialSheetData
from core_logic.interfaces.work_repo import IWorkRepository


class GetRemedialSheetDataUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self, variant_id: str) -> RemedialSheetData:
        return self.work_repo.get_remedial_sheet_data(variant_id)
