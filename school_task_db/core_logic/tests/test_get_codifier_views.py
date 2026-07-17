from unittest import TestCase

from core_logic.use_cases.get_codifier_detail import GetCodifierDetailUseCase
from core_logic.use_cases.get_codifier_list import GetCodifierListUseCase


class FakeCodifierRepository:
    def __init__(self):
        self.codifiers = ['codifier-1']
        self.codifier = 'codifier-1'
        self.content_tree = ['entry-1']
        self.requirements = ['requirement-1']
        self.coverage = {'total': 2, 'covered': 1, 'pct': 50}

    def get_list_codifiers(self):
        return self.codifiers

    def get_codifier(self, codifier_id):
        return self.codifier if codifier_id == self.codifier else None

    def get_content_tree(self, codifier_id):
        return self.content_tree

    def get_requirements(self, codifier_id):
        return self.requirements

    def get_coverage(self, codifier_id):
        return self.coverage


class GetCodifierListUseCaseTests(TestCase):
    def test_execute_returns_codifier_list_data(self):
        repo = FakeCodifierRepository()
        use_case = GetCodifierListUseCase(codifier_repo=repo)

        data = use_case.execute()

        self.assertEqual(data.codifiers, ['codifier-1'])


class GetCodifierDetailUseCaseTests(TestCase):
    def test_execute_returns_codifier_detail_data(self):
        repo = FakeCodifierRepository()
        use_case = GetCodifierDetailUseCase(codifier_repo=repo)

        data = use_case.execute('codifier-1')

        self.assertEqual(data.codifier, 'codifier-1')
        self.assertEqual(data.content_tree, ['entry-1'])
        self.assertEqual(data.requirements, ['requirement-1'])
        self.assertEqual(data.coverage, {'total': 2, 'covered': 1, 'pct': 50})

    def test_execute_returns_empty_data_for_missing_codifier(self):
        repo = FakeCodifierRepository()
        use_case = GetCodifierDetailUseCase(codifier_repo=repo)

        data = use_case.execute('missing-codifier')

        self.assertIsNone(data.codifier)
        self.assertEqual(data.content_tree, [])
        self.assertIsNone(data.requirements)
        self.assertEqual(data.coverage, {})
