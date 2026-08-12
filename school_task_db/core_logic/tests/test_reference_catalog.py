from unittest import TestCase

from core_logic.services.reference_catalog import (
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
