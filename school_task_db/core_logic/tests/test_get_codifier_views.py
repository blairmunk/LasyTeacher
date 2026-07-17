from unittest import TestCase

from core_logic.use_cases.get_codifier_detail import GetCodifierDetailUseCase
from core_logic.use_cases.get_codifier_list import GetCodifierListUseCase


class FakeCodifierRepository:
    def __init__(self):
        self.codifiers = ['codifier-1']
        self.detail_codifiers = ['detail-codifier-1']
        self.content_tree = ['entry-1']
        self.requirements = ['requirement-1']
        self.coverage = {'total': 2, 'covered': 1, 'pct': 50}

    def get_list_codifiers(self):
        return self.codifiers

    def get_detail_codifiers(self):
        return self.detail_codifiers

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
    def test_get_queryset_returns_detail_codifiers(self):
        repo = FakeCodifierRepository()
        use_case = GetCodifierDetailUseCase(codifier_repo=repo)

        self.assertEqual(use_case.get_queryset(), ['detail-codifier-1'])

    def test_execute_returns_codifier_detail_data(self):
        repo = FakeCodifierRepository()
        use_case = GetCodifierDetailUseCase(codifier_repo=repo)

        data = use_case.execute('codifier-1')

        self.assertEqual(data.content_tree, ['entry-1'])
        self.assertEqual(data.requirements, ['requirement-1'])
        self.assertEqual(data.coverage, {'total': 2, 'covered': 1, 'pct': 50})
