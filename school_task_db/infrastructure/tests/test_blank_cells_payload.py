from unittest import TestCase

from infrastructure.services.blank_cells_payload import (
    build_blank_cells_payload,
)


class BlankCellsPayloadTests(TestCase):
    def test_keeps_five_millimetre_cells_on_a4(self):
        payload = build_blank_cells_payload(
            {'area_cm2': 40},
            page_format='A4',
        )

        self.assertEqual(payload['columns'], 37)
        self.assertEqual(payload['rows'], 5)
        self.assertEqual(payload['cell_size_mm'], 5)
        self.assertEqual(payload['css_max_width_mm'], 185)
        self.assertEqual(payload['latex_cell_size_mm'], '5.0')

    def test_adds_rows_on_a5_to_preserve_requested_area(self):
        payload = build_blank_cells_payload(
            {'area_cm2': 40},
            page_format='A5',
        )

        self.assertEqual(payload['columns'], 26)
        self.assertEqual(payload['rows'], 7)
        self.assertEqual(payload['cell_size_mm'], 5)
        self.assertEqual(payload['css_max_width_mm'], 130)
        self.assertGreaterEqual(
            payload['rows'] * payload['columns'] * 0.25,
            40,
        )

    def test_supports_legacy_explicit_grid_dimensions(self):
        payload = build_blank_cells_payload({'rows': 2, 'columns': 3})

        self.assertEqual(payload['rows'], 2)
        self.assertEqual(payload['columns'], 3)
        self.assertEqual(payload['cell_size_mm'], 5)
        self.assertEqual(payload['css_max_width_mm'], 15)
