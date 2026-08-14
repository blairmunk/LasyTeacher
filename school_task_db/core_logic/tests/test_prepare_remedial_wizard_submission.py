from unittest import TestCase
import datetime as dt

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
    def test_create_request_copies_nested_input_collections(self):
        selected_student_ids = ['student-1']
        task_ids = ['task-1']
        student_task_ids = {'student-1': task_ids}

        request = CreateRemedialWizardWorkRequest(
            group_id='group-1',
            selected_student_ids=selected_student_ids,
            student_task_ids=student_task_ids,
            work_name='Работа над ошибками',
            create_event=False,
            event_date=None,
        )

        selected_student_ids.append('student-2')
        task_ids.append('task-2')
        student_task_ids['student-2'] = ['task-3']

        self.assertEqual(request.selected_student_ids, ('student-1',))
        self.assertEqual(
            dict(request.student_task_ids),
            {'student-1': ('task-1',)},
        )

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
                event_date=dt.date(2026, 3, 10),
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

    def test_prepare_create_submission_rejects_invalid_event_date(self):
        result = PrepareRemedialWizardCreateSubmissionUseCase().execute(
            PrepareRemedialWizardSubmissionRequest(
                data={'event_date': ['not-a-date']},
            ),
        )

        self.assertIsNone(result.event_date)
