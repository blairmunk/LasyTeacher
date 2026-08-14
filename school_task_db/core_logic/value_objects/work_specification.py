"""Value objects for work specification rows."""

from dataclasses import dataclass

from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_SPACE_AREA_CM2,
    TASK_BANK_ROLE_ANY,
    TASK_RENDER_MODE_TASK_ONLY,
    validate_task_bank_role,
    validate_task_render_mode,
)


@dataclass(frozen=True)
class WorkTaskSelectionSpec:
    """Specification row for selecting tasks from a bank group."""

    analog_group_id: str
    count: int
    order: int = 0
    bank_role_filter: str = TASK_BANK_ROLE_ANY
    render_mode: str = TASK_RENDER_MODE_TASK_ONLY
    is_assessable: bool = True
    blank_cells_after: bool = False
    blank_space_area_cm2: int = DEFAULT_BLANK_SPACE_AREA_CM2
    page_break_after: bool = False
    weight: int = 1

    def __post_init__(self):
        if not self.analog_group_id:
            raise ValueError('analog_group_id is required')
        if self.count < 1:
            raise ValueError('count must be positive')
        if self.weight < 0:
            raise ValueError('weight must be non-negative')
        if self.blank_space_area_cm2 < 1:
            raise ValueError('blank_space_area_cm2 must be positive')
        validate_task_bank_role(self.bank_role_filter)
        validate_task_render_mode(self.render_mode)
