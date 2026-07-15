"""Build work form screen data."""

from core_logic.entities.work import WorkFormData
from core_logic.interfaces.work_repo import IWorkRepository


class GetWorkFormDataUseCase:
    def __init__(self, work_repo: IWorkRepository):
        self.work_repo = work_repo

    def execute(self) -> WorkFormData:
        return WorkFormData(
            analog_group_options=self.work_repo.get_work_form_analog_group_options(),
        )
