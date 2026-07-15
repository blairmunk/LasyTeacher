"""Build step 1 data for the remedial wizard."""

from dataclasses import dataclass
from typing import List, Tuple

from core_logic.entities.student import StudentGroupRef
from core_logic.interfaces.student_repo import IStudentRepository


LIMIT_CHOICES: Tuple[Tuple[str, str], ...] = (
    ('tasks', 'По количеству заданий'),
    ('weight', 'По суммарному весу (≈ сложность)'),
    ('time', 'По времени выполнения (мин)'),
)


@dataclass(frozen=True)
class RemedialWizardStartData:
    groups: List[StudentGroupRef]
    limit_choices: Tuple[Tuple[str, str], ...] = LIMIT_CHOICES


class GetRemedialWizardStartUseCase:
    def __init__(self, student_repo: IStudentRepository):
        self.student_repo = student_repo

    def execute(self) -> RemedialWizardStartData:
        return RemedialWizardStartData(
            groups=self.student_repo.get_all_student_groups(),
        )
