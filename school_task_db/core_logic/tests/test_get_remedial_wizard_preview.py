from unittest import TestCase

from core_logic.entities.student import RemedialWizardPreviewData, StudentGroupRef
from core_logic.use_cases.get_remedial_wizard_preview import (
    GetRemedialWizardPreviewUseCase,
    RemedialWizardPreviewRequest,
)
from core_logic.use_cases.get_remedial_wizard_start import (
    LIMIT_CHOICES,
    GetRemedialWizardStartUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.request = None
        self.preview_data = RemedialWizardPreviewData(
            group='group',
            preview=[{'student': 'student'}],
            students_with_tasks=1,
            total_tasks=2,
        )
        self.groups = [StudentGroupRef(pk='group-1', name='9А')]

    def get_remedial_wizard_preview_data(
        self,
        group_id,
        threshold,
        limit_type,
        limit_value,
        work_name,
    ):
        self.request = (group_id, threshold, limit_type, limit_value, work_name)
        return self.preview_data

    def get_all_student_groups(self):
        return self.groups


class GetRemedialWizardPreviewUseCaseTests(TestCase):
    def test_execute_returns_repository_data(self):
        repo = FakeStudentRepository()
        use_case = GetRemedialWizardPreviewUseCase(student_repo=repo)

        result = use_case.execute(
            RemedialWizardPreviewRequest(
                group_id='group-1',
                threshold=60,
                limit_type='weight',
                limit_value=15,
                work_name='Повторение',
            )
        )

        self.assertEqual(
            repo.request,
            ('group-1', 60, 'weight', 15, 'Повторение'),
        )
        self.assertEqual(result, repo.preview_data)

    def test_start_use_case_returns_groups_and_limit_choices(self):
        repo = FakeStudentRepository()
        use_case = GetRemedialWizardStartUseCase(student_repo=repo)

        result = use_case.execute()

        self.assertEqual(result.groups, [StudentGroupRef(pk='group-1', name='9А')])
        self.assertEqual(result.limit_choices, LIMIT_CHOICES)
