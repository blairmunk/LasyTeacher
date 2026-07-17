from unittest import TestCase

from core_logic.use_cases.get_variant_generation_form import (
    GetVariantGenerationFormUseCase,
)


class FakeWorkRepository:
    def __init__(self, work='work'):
        self.work = work
        self.work_id = None

    def get_work_generation_target(self, work_id):
        self.work_id = work_id
        return self.work


class GetVariantGenerationFormUseCaseTests(TestCase):
    def test_execute_returns_ready_form_data(self):
        repo = FakeWorkRepository(work='work')
        use_case = GetVariantGenerationFormUseCase(work_repo=repo)

        data = use_case.execute('work-1')

        self.assertEqual(repo.work_id, 'work-1')
        self.assertEqual(data.status, 'ready')
        self.assertEqual(data.work, 'work')

    def test_execute_returns_not_found_status(self):
        repo = FakeWorkRepository(work=None)
        use_case = GetVariantGenerationFormUseCase(work_repo=repo)

        data = use_case.execute('missing')

        self.assertEqual(data.status, 'not_found')
        self.assertIsNone(data.work)
