from unittest import TestCase

from core_logic.entities.student import (
    StudentDetail,
    StudentRemedialCandidateTask,
    StudentRemedialSource,
)
from core_logic.entities.task import TaskEntity
from core_logic.interfaces.work_commands import CreateVariantParams
from core_logic.services.student_remedial_service import StudentRemedialService
from core_logic.use_cases.create_student_remedial_variant import (
    CreateStudentRemedialVariantRequest,
    CreateStudentRemedialVariantUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.requested_student_id = None
        self.source = StudentRemedialSource(
            tasks=(
                StudentRemedialCandidateTask(
                    task_id='task-1',
                    text='Задание 1',
                    analog_group_ids=('group-1',),
                ),
                StudentRemedialCandidateTask(
                    task_id='task-2',
                    text='Задание 2',
                    analog_group_ids=('group-1',),
                ),
            ),
        )

    def get_student_remedial_source(self, student_id):
        self.requested_student_id = student_id
        return self.source

    def get_student(self, student_id):
        return StudentDetail(
            pk=student_id,
            first_name='Иван',
            last_name='Иванов',
            short_name='Иванов И.',
        )


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

    def create_variant_from_plan(self, params: CreateVariantParams):
        self.created_variant_params = params
        return 'variant-1'


class CreateStudentRemedialVariantUseCaseTests(TestCase):
    def test_execute_creates_orphan_remedial_variant(self):
        student_repo = FakeStudentRepository()
        work_repo = FakeWorkRepository()
        use_case = CreateStudentRemedialVariantUseCase(
            student_repo=student_repo,
            student_learning_repo=student_repo,
            task_repo=FakeTaskRepository(),
            work_repo=work_repo,
            remedial_service=StudentRemedialService(
                shuffle=lambda items: None,
            ),
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
        self.assertEqual(student_repo.requested_student_id, 'student-1')
        self.assertEqual(work_repo.created_variant_params.work_id, None)
        self.assertEqual(work_repo.created_variant_params.student_id, 'student-1')
        self.assertEqual(
            work_repo.created_variant_params.plan.work_name_snapshot,
            'Работа над ошибками — Иванов И.',
        )
        self.assertEqual(
            work_repo.created_variant_params.plan.max_score_snapshot,
            5,
        )
        self.assertEqual(
            [
                (
                    task.task_id,
                    task.order,
                    task.content_order,
                    task.max_points,
                    task.bank_role,
                )
                for task in work_repo.created_variant_params.plan.tasks
            ],
            [
                ('task-1', 1, 1, 2, 'remedial'),
                ('task-2', 2, 2, 3, 'remedial'),
            ],
        )

    def test_execute_handles_empty_selection(self):
        student_repo = FakeStudentRepository()
        student_repo.source = StudentRemedialSource()
        use_case = CreateStudentRemedialVariantUseCase(
            student_repo=student_repo,
            student_learning_repo=student_repo,
            task_repo=FakeTaskRepository(),
            work_repo=FakeWorkRepository(),
            remedial_service=StudentRemedialService(
                shuffle=lambda items: None,
            ),
        )

        result = use_case.execute(
            CreateStudentRemedialVariantRequest(student_id='student-1')
        )

        self.assertFalse(result.success)
        self.assertEqual(
            result.message,
            'Нет доступных заданий для работы над ошибками.',
        )
