from unittest import TestCase

from core_logic.use_cases.change_task_group_membership import (
    AddTasksToGroupRequest,
    UpdateTaskGroupRolesRequest,
)
from core_logic.use_cases.prepare_task_group_membership_submission import (
    PrepareAddTasksToGroupSubmissionRequest,
    PrepareAddTasksToGroupSubmissionUseCase,
    PrepareUpdateTaskGroupRolesSubmissionRequest,
    PrepareUpdateTaskGroupRolesSubmissionUseCase,
)
from core_logic.value_objects.variant_print_plan import TASK_BANK_ROLE_DEMO


class PrepareTaskGroupMembershipSubmissionUseCaseTests(TestCase):
    def test_prepare_add_tasks_to_group_submission(self):
        result = PrepareAddTasksToGroupSubmissionUseCase().execute(
            PrepareAddTasksToGroupSubmissionRequest(
                group_id='group-1',
                data={
                    'selected_tasks': ['task-1', 'task-2'],
                    'bank_role': [TASK_BANK_ROLE_DEMO],
                },
            )
        )

        self.assertEqual(
            result,
            AddTasksToGroupRequest(
                group_id='group-1',
                task_ids=['task-1', 'task-2'],
                bank_role=TASK_BANK_ROLE_DEMO,
            ),
        )

    def test_prepare_add_tasks_to_group_submission_uses_empty_default(self):
        result = PrepareAddTasksToGroupSubmissionUseCase().execute(
            PrepareAddTasksToGroupSubmissionRequest(
                group_id='group-1',
                data={},
            )
        )

        self.assertEqual(result.task_ids, [])
        self.assertEqual(result.bank_role, 'control')

    def test_prepare_update_task_group_roles_submission(self):
        result = PrepareUpdateTaskGroupRolesSubmissionUseCase().execute(
            PrepareUpdateTaskGroupRolesSubmissionRequest(
                group_id='group-1',
                data={
                    'task_role_task-1': [TASK_BANK_ROLE_DEMO],
                    'selected_tasks': ['ignored'],
                },
            )
        )

        self.assertEqual(
            result,
            UpdateTaskGroupRolesRequest(
                group_id='group-1',
                task_roles={'task-1': TASK_BANK_ROLE_DEMO},
            ),
        )
