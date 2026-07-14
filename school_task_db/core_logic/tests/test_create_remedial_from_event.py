from unittest import TestCase

from core_logic.entities.event import EventEntity, MarkEntity
from core_logic.entities.task import TaskEntity
from core_logic.interfaces.work_repo import CreateVariantParams, CreateWorkParams
from core_logic.services.remedial_service import RemedialTaskSelection
from core_logic.use_cases.create_remedial_from_event import (
    CreateRemedialFromEventUseCase,
    RemedialFromEventRequest,
)


class FakeRemedialService:
    def __init__(self):
        self.calls = []

    def select_tasks_for_student(
        self,
        student_id,
        event_id,
        source_work_id,
        mark_score=None,
    ):
        self.calls.append((student_id, event_id, source_work_id, mark_score))
        return RemedialTaskSelection(
            student_id=student_id,
            task_ids=['t10'],
            weak_group_ids={'g1'},
            target_difficulty=3,
        )


class FakeTaskRepository:
    def get_by_ids(self, task_ids):
        return [TaskEntity(id='t10', difficulty=3)]


class FakeWorkRepository:
    def __init__(self):
        self.created_work = None
        self.created_variants = []

    def create_work(self, params: CreateWorkParams):
        self.created_work = params
        return 'new-work'

    def create_variant_with_tasks(self, params: CreateVariantParams):
        self.created_variants.append(params)
        return f'variant-{params.number}'


class FakeEventRepository:
    def __init__(self):
        self.created_event = None
        self.created_participations = []

    def get_by_id(self, event_id):
        return EventEntity(
            id=event_id,
            name='КР',
            work_id='source-work',
            work_name='Контрольная',
            course_id='course-1',
        )

    def get_student_mark(self, event_id, student_id):
        return MarkEntity(student_id=student_id, event_id=event_id, score=2)

    def create_event(self, params):
        self.created_event = params
        return 'new-event'

    def create_participation(self, event_id, student_id, variant_id):
        self.created_participations.append((event_id, student_id, variant_id))
        return 'participation-1'


class CreateRemedialFromEventUseCaseTests(TestCase):
    def test_execute_creates_work_variants_event_and_participations(self):
        remedial_service = FakeRemedialService()
        task_repo = FakeTaskRepository()
        work_repo = FakeWorkRepository()
        event_repo = FakeEventRepository()
        use_case = CreateRemedialFromEventUseCase(
            remedial_service=remedial_service,
            task_repo=task_repo,
            work_repo=work_repo,
            event_repo=event_repo,
        )

        result = use_case.execute(
            RemedialFromEventRequest(
                event_id='event-1',
                selected_student_ids=['student-1'],
                work_name='Работа над ошибками',
                create_event=True,
                event_date='2026-03-10',
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.work_id, 'new-work')
        self.assertEqual(result.event_id, 'new-event')
        self.assertEqual(result.variants_created, 1)
        self.assertEqual(
            remedial_service.calls,
            [('student-1', 'event-1', 'source-work', 2)],
        )
        self.assertEqual(
            work_repo.created_work,
            CreateWorkParams(
                name='Работа над ошибками',
                work_type='remedial',
                max_score=3,
                variant_counter=1,
            ),
        )
        self.assertEqual(len(work_repo.created_variants), 1)
        self.assertEqual(work_repo.created_variants[0].task_ids, ['t10'])
        self.assertEqual(work_repo.created_variants[0].max_score_snapshot, 3)
        self.assertEqual(event_repo.created_event.work_id, 'new-work')
        self.assertEqual(
            event_repo.created_participations,
            [('new-event', 'student-1', 'variant-1')],
        )

    def test_execute_without_selected_students_returns_warning_result(self):
        use_case = CreateRemedialFromEventUseCase(
            remedial_service=FakeRemedialService(),
            task_repo=FakeTaskRepository(),
            work_repo=FakeWorkRepository(),
            event_repo=FakeEventRepository(),
        )

        result = use_case.execute(
            RemedialFromEventRequest(
                event_id='event-1',
                selected_student_ids=[],
            )
        )

        self.assertFalse(result.success)
        self.assertEqual(result.message, 'Не выбрано ни одного ученика.')
