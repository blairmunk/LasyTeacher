"""Renderer-ready geometry for fixed-size notebook grids."""

from math import ceil

from core_logic.value_objects.task_print_settings import (
    BLANK_CELL_SIZE_MM,
    DEFAULT_BLANK_CELLS_COLUMNS,
    DEFAULT_BLANK_CELLS_ROWS,
)

PRINTABLE_WIDTH_MM = {
    'A4': 186,
    'A5': 130,
}


def build_blank_cells_payload(options, page_format='A4'):
    options = dict(options)
    area_cm2 = _optional_positive_int(options.get('area_cm2'), max_value=500)
    if area_cm2 is None:
        rows = _positive_int(
            options.get('rows'),
            default=DEFAULT_BLANK_CELLS_ROWS,
            max_value=100,
        )
        columns = _positive_int(
            options.get('columns'),
            default=DEFAULT_BLANK_CELLS_COLUMNS,
            max_value=100,
        )
    else:
        columns = _page_columns(page_format)
        rows = ceil(_cell_count(area_cm2) / columns)
    return {
        **options,
        'area_cm2': area_cm2,
        'rows': rows,
        'columns': columns,
        'cell_size_mm': BLANK_CELL_SIZE_MM,
        'css_max_width_mm': columns * BLANK_CELL_SIZE_MM,
        'rows_range': range(rows),
        'cells_range': range(rows * columns),
        'latex_cell_size_mm': f'{BLANK_CELL_SIZE_MM:.1f}',
    }


def _positive_int(value, default, max_value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < 1:
        return default
    return min(parsed, max_value)


def _optional_positive_int(value, max_value):
    if value in (None, ''):
        return None
    return _positive_int(value, default=1, max_value=max_value)


def _page_columns(page_format):
    printable_width = PRINTABLE_WIDTH_MM.get(
        str(page_format).upper(),
        PRINTABLE_WIDTH_MM['A4'],
    )
    return max(1, printable_width // BLANK_CELL_SIZE_MM)


def _cell_count(area_cm2):
    cell_area_cm2 = (BLANK_CELL_SIZE_MM / 10) ** 2
    return ceil(area_cm2 / cell_area_cm2)
