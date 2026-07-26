"""Build work form screen data."""

from core_logic.entities.work import WorkFormData
from core_logic.interfaces.work_read_repo import IWorkReadRepository


class GetWorkFormDataUseCase:
    def __init__(self, work_read_repo: IWorkReadRepository):
        self.work_read_repo = work_read_repo

    def execute(self) -> WorkFormData:
        return WorkFormData(
            analog_group_options=(
                self.work_read_repo.get_work_form_analog_group_options()
            ),
        )
