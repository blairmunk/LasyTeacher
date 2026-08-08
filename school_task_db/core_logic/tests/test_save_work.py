from unittest import TestCase

from core_logic.interfaces.work_repo import (
    CreateWorkParams,
    CreateWorkWithSpecificationParams,
    WorkContentBlockParams,
    WorkTaskSelectionParams,
    WorkUpdateContext,
)
from core_logic.use_cases.save_work import (
    CreateWorkWithSpecificationUseCase,
    UpdateWorkWithSpecificationRequest,
    UpdateWorkWithSpecificationUseCase,
)
from core_logic.value_objects.work_assessment import (
    WORK_ASSESSMENT_MODE_AGGREGATE,
    WORK_ASSESSMENT_MODE_VARIANT,
)


class FakeWorkRepository:
    def __init__(self, update_result=True):
        self.created_with_specification = None
        self.updated_with_specification = None
        self.update_result = update_result
        self.update_context = WorkUpdateContext(
            work_id='work-1',
            assessment_mode=WORK_ASSESSMENT_MODE_VARIANT,
        )

    def create_work_with_specification(self, params):
        self.created_with_specification = params
        return 'work-with-specification'

    def get_work_update_context(self, work_id):
        if not self.update_result or work_id != self.update_context.work_id:
            return None
        return self.update_context

    def update_work_with_specification(self, params):
        self.updated_with_specification = params
        return self.update_result

class SaveWorkUseCaseTests(TestCase):
    def test_create_work_with_specification_validates_and_delegates(self):
        repo = FakeWorkRepository()
        params = CreateWorkWithSpecificationParams(
            work=CreateWorkParams(name='Рабочий лист'),
            specs=[
                WorkTaskSelectionParams(
                    analog_group_id='group-1',
                    order=1,
                    count=2,
                    weight=3,
                )
            ],
        )

        result = CreateWorkWithSpecificationUseCase(repo).execute(params)

        self.assertEqual(result.status, 'created')
        self.assertEqual(result.work_id, 'work-with-specification')
        self.assertEqual(repo.created_with_specification, params)

    def test_create_work_validates_persistent_content_blocks(self):
        repo = FakeWorkRepository()
        params = CreateWorkWithSpecificationParams(
            work=CreateWorkParams(name='Рабочий лист'),
            specs=[],
            content_blocks=[
                WorkContentBlockParams(
                    content_type='theory',
                    order=10,
                    title='Теория',
                    topic_ids=['topic-1'],
                ),
                WorkContentBlockParams(
                    content_type='text',
                    order=20,
                    title='Инструкция',
                    body='Покажите ход решения.',
                ),
            ],
        )

        result = CreateWorkWithSpecificationUseCase(repo).execute(params)

        self.assertEqual(result.status, 'created')
        self.assertEqual(repo.created_with_specification, params)

    def test_create_work_with_specification_rejects_invalid_specs(self):
        repo = FakeWorkRepository()
        params = CreateWorkWithSpecificationParams(
            work=CreateWorkParams(name='Рабочий лист'),
            specs=[
                WorkTaskSelectionParams(
                    analog_group_id='group-1',
                    order=1,
                    count=1,
                    weight=1,
                    blank_cells_rows=0,
                )
            ],
        )

        result = CreateWorkWithSpecificationUseCase(repo).execute(params)

        self.assertEqual(result.status, 'invalid')
        self.assertIn('blank_cells_rows must be positive', result.errors[0])
        self.assertIsNone(repo.created_with_specification)

    def test_update_work_with_specification_delegates_complete_change(self):
        repo = FakeWorkRepository()
        work = CreateWorkParams(
            work_id='work-1',
            name='Обновлённая работа',
        )
        specs = [
            WorkTaskSelectionParams(
                analog_group_id='group-1',
                order=10,
                count=2,
                weight=3,
            ),
        ]

        result = UpdateWorkWithSpecificationUseCase(repo).execute(
            UpdateWorkWithSpecificationRequest(work=work, specs=specs),
        )

        self.assertEqual(result.status, 'updated')
        self.assertEqual(
            repo.updated_with_specification,
            CreateWorkWithSpecificationParams(work=work, specs=specs),
        )

    def test_combined_update_allows_mode_change_before_work_is_used(self):
        repo = FakeWorkRepository()
        work = CreateWorkParams(
            work_id='work-1',
            name='Внешний материал',
            assessment_mode=WORK_ASSESSMENT_MODE_AGGREGATE,
        )

        result = UpdateWorkWithSpecificationUseCase(repo).execute(
            UpdateWorkWithSpecificationRequest(work=work, specs=[]),
        )

        self.assertEqual(result.status, 'updated')
        self.assertEqual(
            repo.updated_with_specification.work.assessment_mode,
            WORK_ASSESSMENT_MODE_AGGREGATE,
        )

    def test_combined_update_rejects_mode_change_after_event(self):
        repo = FakeWorkRepository()
        repo.update_context = WorkUpdateContext(
            work_id='work-1',
            assessment_mode=WORK_ASSESSMENT_MODE_VARIANT,
            has_events=True,
        )
        work = CreateWorkParams(
            work_id='work-1',
            name='Не сохранять',
            assessment_mode=WORK_ASSESSMENT_MODE_AGGREGATE,
        )

        result = UpdateWorkWithSpecificationUseCase(repo).execute(
            UpdateWorkWithSpecificationRequest(work=work, specs=[]),
        )

        self.assertEqual(result.status, 'invalid')
        self.assertIsNone(repo.updated_with_specification)

    def test_combined_update_rejects_duplicate_content_order(self):
        repo = FakeWorkRepository()

        result = UpdateWorkWithSpecificationUseCase(repo).execute(
            UpdateWorkWithSpecificationRequest(
                work=CreateWorkParams(work_id='work-1', name='КР'),
                specs=[
                    WorkTaskSelectionParams(
                        analog_group_id='group-1',
                        order=10,
                        count=1,
                        weight=1,
                    ),
                ],
                content_blocks=[
                    WorkContentBlockParams(
                        content_type='text',
                        order=10,
                        body='Инструкция',
                    ),
                ],
            )
        )

        self.assertEqual(result.status, 'invalid')
        self.assertIn('уникальным', result.errors[0])
        self.assertIsNone(repo.updated_with_specification)

    def test_combined_update_returns_not_found(self):
        result = UpdateWorkWithSpecificationUseCase(
            FakeWorkRepository(False),
        ).execute(
            UpdateWorkWithSpecificationRequest(
                work=CreateWorkParams(work_id='missing', name='КР'),
                specs=[],
            ),
        )

        self.assertEqual(result.status, 'not_found')
