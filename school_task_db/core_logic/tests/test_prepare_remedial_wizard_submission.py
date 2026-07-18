from unittest import TestCase

from core_logic.use_cases.create_remedial_wizard_work import (
    CreateRemedialWizardWorkRequest,
)
from core_logic.use_cases.get_remedial_wizard_preview import (
    RemedialWizardPreviewRequest,
)
from core_logic.use_cases.prepare_remedial_wizard_submission import (
    PrepareRemedialWizardCreateSubmissionUseCase,
    PrepareRemedialWizardPreviewSubmissionUseCase,
    PrepareRemedialWizardSubmissionRequest,
)


class PrepareRemedialWizardSubmissionUseCaseTests(TestCase):
    def test_prepare_preview_submission_parses_parameters(self):
        result = PrepareRemedialWizardPreviewSubmissionUseCase().execute(
            PrepareRemedialWizardSubmissionRequest(
                data={
                    'group_id': ['group-1'],
                    'threshold': ['65'],
                    'limit_type': ['weight'],
                    'limit_value': ['15'],
                    'work_name': ['Повторение'],
                },
            )
        )

        self.assertEqual(
            result,
            RemedialWizardPreviewRequest(
                group_id='group-1',
                threshold=65,
                limit_type='weight',
                limit_value=15,
                work_name='Повторение',
            ),
        )

    def test_prepare_preview_submission_uses_defaults_for_invalid_numbers(self):
        result = PrepareRemedialWizardPreviewSubmissionUseCase().execute(
            PrepareRemedialWizardSubmissionRequest(
                data={
                    'group_id': ['group-1'],
                    'threshold': ['bad'],
                    'limit_value': ['bad'],
                },
            )
        )

        self.assertEqual(result.threshold, 70)
        self.assertEqual(result.limit_value, 10)
        self.assertEqual(result.limit_type, 'tasks')
        self.assertEqual(result.work_name, 'Работа над ошибками')

    def test_prepare_create_submission_parses_selected_student_tasks(self):
        result = PrepareRemedialWizardCreateSubmissionUseCase().execute(
            PrepareRemedialWizardSubmissionRequest(
                data={
                    'group_id': ['group-1'],
                    'work_name': ['Работа над ошибками 9А'],
                    'create_event': ['1'],
                    'event_date': ['2026-03-10'],
                    'selected_students': ['student-1', 'student-2'],
                    'task_ids_student-1': ['task-1, task-2,,'],
                    'task_ids_student-2': ['task-3'],
                },
            )
        )

        self.assertEqual(
            result,
            CreateRemedialWizardWorkRequest(
                group_id='group-1',
                selected_student_ids=['student-1', 'student-2'],
                student_task_ids={
                    'student-1': ['task-1', 'task-2'],
                    'student-2': ['task-3'],
                },
                work_name='Работа над ошибками 9А',
                create_event=True,
                event_date='2026-03-10',
            ),
        )

    def test_prepare_create_submission_ignores_tasks_for_unselected_students(self):
        result = PrepareRemedialWizardCreateSubmissionUseCase().execute(
            PrepareRemedialWizardSubmissionRequest(
                data={
                    'group_id': ['group-1'],
                    'selected_students': ['student-1'],
                    'task_ids_student-2': ['task-3'],
                },
            )
        )

        self.assertEqual(result.student_task_ids, {})
        self.assertFalse(result.create_event)
