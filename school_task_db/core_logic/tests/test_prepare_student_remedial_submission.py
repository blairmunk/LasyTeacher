from unittest import TestCase

from core_logic.use_cases.create_student_remedial_variant import (
    CreateStudentRemedialVariantRequest,
)
from core_logic.use_cases.prepare_student_remedial_submission import (
    PrepareStudentRemedialSubmissionRequest,
    PrepareStudentRemedialSubmissionUseCase,
)


class PrepareStudentRemedialSubmissionUseCaseTests(TestCase):
    def test_execute_prepares_creation_request(self):
        result = PrepareStudentRemedialSubmissionUseCase().execute(
            PrepareStudentRemedialSubmissionRequest(
                student_id='student-1',
                data={
                    'max_tasks': ['5'],
                    'groups': ['group-1', 'group-2'],
                },
            )
        )

        self.assertEqual(
            result,
            CreateStudentRemedialVariantRequest(
                student_id='student-1',
                max_tasks=5,
                selected_group_ids=['group-1', 'group-2'],
            ),
        )

    def test_execute_uses_defaults_for_missing_values(self):
        result = PrepareStudentRemedialSubmissionUseCase().execute(
            PrepareStudentRemedialSubmissionRequest(
                student_id='student-1',
                data={},
            )
        )

        self.assertEqual(result.max_tasks, 10)
        self.assertEqual(result.selected_group_ids, [])

    def test_execute_uses_default_for_invalid_max_tasks(self):
        result = PrepareStudentRemedialSubmissionUseCase().execute(
            PrepareStudentRemedialSubmissionRequest(
                student_id='student-1',
                data={'max_tasks': ['bad']},
            )
        )

        self.assertEqual(result.max_tasks, 10)
