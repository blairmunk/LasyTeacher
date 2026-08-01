from unittest import TestCase

from core_logic.entities.work import (
    VariantGenerationGroupSource,
    VariantGenerationWork,
)
from core_logic.use_cases.get_variant_generation_form import (
    GetVariantGenerationFormUseCase,
)


class FakeWorkRepository:
    def __init__(self, work=None):
        if work is None:
            work = VariantGenerationWork(
                pk='work-1',
                name='Работа',
                duration=45,
                variant_counter=0,
            )
        self.work = work
        self.groups = [VariantGenerationGroupSource(
            group_name='Динамика',
            requested_count=1,
            bank_role_filter='practice',
            task_bank_roles=('demo', 'practice', 'practice'),
        )]
        self.work_id = None
        self.groups_work_id = None

    def get_work_generation_target(self, work_id):
        self.work_id = work_id
        return self.work

    def get_variant_generation_group_sources(self, work_id):
        self.groups_work_id = work_id
        return self.groups


class GetVariantGenerationFormUseCaseTests(TestCase):
    def test_execute_returns_ready_form_data(self):
        repo = FakeWorkRepository()
        use_case = GetVariantGenerationFormUseCase(work_repo=repo)

        data = use_case.execute('work-1')

        self.assertEqual(repo.work_id, 'work-1')
        self.assertEqual(repo.groups_work_id, 'work-1')
        self.assertEqual(data.status, 'ready')
        self.assertEqual(data.work.pk, 'work-1')
        self.assertEqual(data.work_groups[0].group_name, 'Динамика')
        self.assertEqual(data.work_groups[0].available_count, 2)

    def test_execute_returns_not_found_status(self):
        repo = FakeWorkRepository(work=False)
        use_case = GetVariantGenerationFormUseCase(work_repo=repo)

        data = use_case.execute('missing')

        self.assertEqual(data.status, 'not_found')
        self.assertIsNone(data.work)
        self.assertEqual(data.work_groups, [])
