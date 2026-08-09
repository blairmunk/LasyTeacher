from unittest import TestCase

from core_logic.services.reference_catalog import (
    merge_reference_choices,
    parse_simple_reference_items,
    parse_subject_reference_items,
)


class ReferenceCatalogTests(TestCase):
    def test_parses_simple_reference_lines(self):
        self.assertEqual(
            parse_simple_reference_items(' Физика\n\n Математика  \n'),
            ['Физика', 'Математика'],
        )

    def test_parses_coded_and_plain_subject_reference_lines(self):
        self.assertEqual(
            parse_subject_reference_items(
                '1.1 | Механическое движение\nЭнергия\ninvalid|\n',
            ),
            [
                ('1.1', 'Механическое движение'),
                ('Энергия', 'Энергия'),
            ],
        )

    def test_merges_catalogs_without_duplicate_codes(self):
        self.assertEqual(
            merge_reference_choices([
                [('1.1', 'Первое название')],
                [('1.1', 'Другое название'), ('1.2', 'Второй элемент')],
            ]),
            [('1.1', 'Первое название'), ('1.2', 'Второй элемент')],
        )
