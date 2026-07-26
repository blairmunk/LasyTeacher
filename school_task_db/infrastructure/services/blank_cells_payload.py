"""Renderer-ready values shared by document payload builders."""

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_COLUMNS,
    DEFAULT_BLANK_CELLS_ROW_HEIGHT,
    DEFAULT_BLANK_CELLS_ROWS,
)


def build_blank_cells_payload(options):
    options = dict(options)
    rows = _positive_int(
        options.get('rows'),
        default=DEFAULT_BLANK_CELLS_ROWS,
        max_value=40,
    )
    columns = _positive_int(
        options.get('columns'),
        default=DEFAULT_BLANK_CELLS_COLUMNS,
        max_value=40,
    )
    row_height = _positive_int(
        options.get('row_height'),
        default=DEFAULT_BLANK_CELLS_ROW_HEIGHT,
        max_value=120,
    )
    return {
        **options,
        'rows': rows,
        'columns': columns,
        'row_height': row_height,
        'rows_range': range(rows),
        'cells_range': range(rows * columns),
        'latex_cells': _blank_cells_latex_cells(columns, row_height),
    }


def _positive_int(value, default, max_value):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    if parsed < 1:
        return default
    return min(parsed, max_value)


def _blank_cells_latex_cells(columns, row_height):
    cells = [''] * columns
    cells[0] = rf'\rule{{0pt}}{{{row_height / 3:.1f}mm}}'
    return cells
