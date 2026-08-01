from unittest import TestCase

from core_logic.services.codifier_service import CodifierService


class CodifierServiceTests(TestCase):
    def test_builds_natural_content_code_sort_key(self):
        codes = ['2', '1.10', '1.2', '1.2.1']

        result = sorted(codes, key=CodifierService.content_code_sort_key)

        self.assertEqual(result, ['1.2', '1.2.1', '1.10', '2'])

    def test_calculates_coverage(self):
        self.assertEqual(
            CodifierService.coverage(total=4, covered=3),
            {
                'total': 4,
                'covered': 3,
                'uncovered': 1,
                'pct': 75,
            },
        )
        self.assertEqual(
            CodifierService.coverage(total=0, covered=0),
            {
                'total': 0,
                'covered': 0,
                'uncovered': 0,
                'pct': 0,
            },
        )
