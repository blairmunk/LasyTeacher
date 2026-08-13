from contextlib import contextmanager
from unittest import TestCase
import datetime as dt

from core_logic.entities.task import TaskEntity
from core_logic.entities.work_specification_commands import CreateWorkParams
from core_logic.entities.work_variant_creation_commands import (
    CreatedWorkWithVariantsRef,
    CreateWorkWithVariantsParams,
)
from core_logic.use_cases.create_remedial_wizard_work import (
    CreateRemedialWizardWorkRequest,
    CreateRemedialWizardWorkUseCase,
)


class FakeStudentRepository:
    def __init__(self):
        self.group_name = '9А'

    def get_group_name(self, group_id):
        return self.group_name


class FakeTaskRepository:
    def get_by_ids(self, task_ids):
        tasks = {
            'task-1': TaskEntity(id='task-1', difficulty=2),
            'task-2': TaskEntity(id='task-2', difficulty=3),
            'task-3': TaskEntity(id='task-3', difficulty=5),
        }
        return [tasks[task_id] for task_id in task_ids if task_id in tasks]


class FakeWorkRepository:
    def __init__(self):
        self.created_work = None
        self.created_variants = []

    def create_work_with_variants(self, params: CreateWorkWithVariantsParams):
        self.created_work = params.work
        self.created_variants = params.variants
        return CreatedWorkWithVariantsRef(
            work_id='work-1',
            variant_ids=[
                f'variant-{variant.plan.number}'
                for variant in params.variants
            ],
        )


class FakeEventRepository:
    def __init__(self):
        self.created_event = None
        self.created_participations = []

    def create_event(self, params):
        self.created_event = params
        return 'event-1'

    def create_participation(self, event_id, student_id, variant_id):
        self.created_participations.append((event_id, student_id, variant_id))
        return 'participation-1'


class FakeTransactionManager:
    def __init__(self):
        self.entered = 0

    @contextmanager
    def atomic(self):
        self.entered += 1
        yield


class CreateRemedialWizardWorkUseCaseTests(TestCase):
    def test_execute_creates_work_variants_event_and_participations(self):
        work_repo = FakeWorkRepository()
        event_repo = FakeEventRepository()
        transaction_manager = FakeTransactionManager()
        use_case = CreateRemedialWizardWorkUseCase(
            student_repo=FakeStudentRepository(),
            task_repo=FakeTaskRepository(),
            work_repo=work_repo,
            event_write_repo=event_repo,
            event_participation_repo=event_repo,
            transaction_manager=transaction_manager,
        )

        result = use_case.execute(
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
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.work_id, 'work-1')
        self.assertEqual(result.event_id, 'event-1')
        self.assertEqual(result.variants_created, 2)
        self.assertEqual(
            work_repo.created_work,
            CreateWorkParams(
                name='Работа над ошибками 9А',
                work_type='remedial',
                max_score=5,
                variant_counter=2,
            ),
        )
        self.assertEqual(len(work_repo.created_variants), 2)
        self.assertEqual(work_repo.created_variants[0].student_id, 'student-1')
        self.assertEqual(
            [
                task.task_id
                for task in work_repo.created_variants[0].plan.tasks
            ],
            ['task-1', 'task-2'],
        )
        self.assertEqual(
            [
                task.bank_role
                for task in work_repo.created_variants[0].plan.tasks
            ],
            ['remedial', 'remedial'],
        )
        self.assertEqual(work_repo.created_variants[1].student_id, 'student-2')
        self.assertEqual(
            work_repo.created_variants[1].plan.max_score_snapshot,
            5,
        )
        self.assertEqual(event_repo.created_event.work_id, 'work-1')
        self.assertEqual(
            event_repo.created_event.description,
            'Работа над ошибками для 9А',
        )
        self.assertEqual(
            event_repo.created_participations,
            [
                ('event-1', 'student-1', 'variant-1'),
                ('event-1', 'student-2', 'variant-2'),
            ],
        )
        self.assertEqual(transaction_manager.entered, 1)

    def test_execute_handles_empty_selection(self):
        transaction_manager = FakeTransactionManager()
        use_case = CreateRemedialWizardWorkUseCase(
            student_repo=FakeStudentRepository(),
            task_repo=FakeTaskRepository(),
            work_repo=FakeWorkRepository(),
            event_write_repo=FakeEventRepository(),
            event_participation_repo=FakeEventRepository(),
            transaction_manager=transaction_manager,
        )

        result = use_case.execute(
            CreateRemedialWizardWorkRequest(
                group_id='group-1',
                selected_student_ids=[],
                student_task_ids={},
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.status, 'empty_selection')
        self.assertEqual(result.message, 'Не выбрано ни одного ученика.')
        self.assertEqual(transaction_manager.entered, 0)
