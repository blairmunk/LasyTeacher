import datetime as dt
from unittest import TestCase

from core_logic.entities.student_import import StudentImportValidationError
from core_logic.services.student_csv_import_parser import (
    parse_student_csv_rows,
)


class StudentCsvImportParserTests(TestCase):
    def test_parses_russian_aliases_and_academic_year_dates(self):
        rows = parse_student_csv_rows([
            {
                'класс': ' 8А ',
                'учебный_год': '2026–2027',
                'фамилия': ' Иванов ',
                'имя': ' Иван ',
                'отчество': ' Петрович ',
                'почта': ' ivanov@example.test ',
            },
        ])

        row = rows[0]
        self.assertEqual(row.row_number, 2)
        self.assertEqual(row.group_name, '8А')
        self.assertEqual(row.last_name, 'Иванов')
        self.assertEqual(row.email, 'ivanov@example.test')
        self.assertEqual(row.academic_year_start, dt.date(2026, 9, 1))
        self.assertEqual(row.academic_year_end, dt.date(2027, 8, 31))

    def test_reports_required_field_with_csv_row_number(self):
        with self.assertRaisesRegex(
            StudentImportValidationError,
            'Строка 2: класс обязателен',
        ):
            parse_student_csv_rows([
                {'class': '', 'last_name': 'Иванов', 'first_name': 'Иван'},
            ])

    def test_rejects_non_consecutive_academic_year(self):
        with self.assertRaisesRegex(
            StudentImportValidationError,
            'два соседних года',
        ):
            parse_student_csv_rows([
                {
                    'class': '8А',
                    'academic_year': '2026-2028',
                    'last_name': 'Иванов',
                    'first_name': 'Иван',
                },
            ])
