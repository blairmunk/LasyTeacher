from unittest import TestCase

from core_logic.entities.task import TaskEntity
from core_logic.interfaces.work_repo import CreateVariantParams
from core_logic.use_cases.create_student_remedial_variant import (
    CreateStudentRemedialVariantRequest,
    CreateStudentRemedialVariantUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.selected_request = None
        self.short_name = 'Иванов И.'
        self.task_ids = ['task-1', 'task-2']

    def select_student_remedial_task_ids(
        self,
        student_id,
        max_tasks,
        selected_group_ids,
    ):
        self.selected_request = (student_id, max_tasks, selected_group_ids)
        return self.task_ids

    def get_student_short_name(self, student_id):
        return self.short_name


class FakeTaskRepository:
    def get_by_ids(self, task_ids):
        tasks = {
            'task-1': TaskEntity(id='task-1', difficulty=2),
            'task-2': TaskEntity(id='task-2', difficulty=3),
        }
        return [tasks[task_id] for task_id in task_ids if task_id in tasks]


class FakeWorkRepository:
    def __init__(self):
        self.created_variant_params = None

    def create_variant_with_tasks(self, params: CreateVariantParams):
        self.created_variant_params = params
        return 'variant-1'


class CreateStudentRemedialVariantUseCaseTests(TestCase):
    def test_execute_creates_orphan_remedial_variant(self):
        student_repo = FakeStudentRepository()
        work_repo = FakeWorkRepository()
        use_case = CreateStudentRemedialVariantUseCase(
            student_repo=student_repo,
            task_repo=FakeTaskRepository(),
            work_repo=work_repo,
        )

        result = use_case.execute(
            CreateStudentRemedialVariantRequest(
                student_id='student-1',
                max_tasks=5,
                selected_group_ids=['group-1'],
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.variant_id, 'variant-1')
        self.assertEqual(result.task_count, 2)
        self.assertEqual(result.total_score, 5)
        self.assertEqual(
            student_repo.selected_request,
            ('student-1', 5, ['group-1']),
        )
        self.assertEqual(work_repo.created_variant_params.work_id, None)
        self.assertEqual(work_repo.created_variant_params.student_id, 'student-1')
        self.assertEqual(
            work_repo.created_variant_params.work_name_snapshot,
            'Работа над ошибками — Иванов И.',
        )
        self.assertEqual(work_repo.created_variant_params.max_score_snapshot, 5)

    def test_execute_handles_empty_selection(self):
        student_repo = FakeStudentRepository()
        student_repo.task_ids = []
        use_case = CreateStudentRemedialVariantUseCase(
            student_repo=student_repo,
            task_repo=FakeTaskRepository(),
            work_repo=FakeWorkRepository(),
        )

        result = use_case.execute(
            CreateStudentRemedialVariantRequest(student_id='student-1')
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.message,
            'Нет доступных заданий для работы над ошибками.',
        )
