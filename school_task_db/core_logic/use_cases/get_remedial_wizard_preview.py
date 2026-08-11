"""Build preview data for class remedial wizard step 2."""

from dataclasses import dataclass

from core_logic.entities.student import RemedialWizardPreviewData
from core_logic.interfaces.student_remedial_repo import (
    IStudentRemedialRepository,
)
from core_logic.services.remedial_wizard_service import RemedialWizardService


@dataclass(frozen=True)
class RemedialWizardPreviewRequest:
    group_id: str
    threshold: int = 70
    limit_type: str = 'tasks'
    limit_value: int = 10
    work_name: str = 'Работа над ошибками'


class GetRemedialWizardPreviewUseCase:
    def __init__(
        self,
        student_learning_repo: IStudentRemedialRepository,
        service: RemedialWizardService | None = None,
    ):
        self.student_learning_repo = student_learning_repo
        self.service = service or RemedialWizardService()

    def execute(
        self,
        request: RemedialWizardPreviewRequest,
    ) -> RemedialWizardPreviewData:
        return self.service.build(
            self.student_learning_repo.get_remedial_wizard_preview_source(
                request.group_id,
            ),
            threshold=request.threshold,
            limit_type=request.limit_type,
            limit_value=request.limit_value,
            work_name=request.work_name,
        )
