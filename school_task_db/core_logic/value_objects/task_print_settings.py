"""Shared task role and rendering settings."""


TASK_BANK_ROLE_ANY = 'any'
TASK_BANK_ROLE_DEMO = 'demo'
TASK_BANK_ROLE_PRACTICE = 'practice'
TASK_BANK_ROLE_CONTROL = 'control'
TASK_BANK_ROLE_REMEDIAL = 'remedial'

TASK_BANK_ROLES = frozenset(
    (
        TASK_BANK_ROLE_ANY,
        TASK_BANK_ROLE_DEMO,
        TASK_BANK_ROLE_PRACTICE,
        TASK_BANK_ROLE_CONTROL,
        TASK_BANK_ROLE_REMEDIAL,
    )
)
TASK_BANK_SPECIFIC_ROLES = frozenset(
    role for role in TASK_BANK_ROLES if role != TASK_BANK_ROLE_ANY
)

TASK_BANK_ROLE_LABELS = {
    TASK_BANK_ROLE_ANY: 'Любая роль',
    TASK_BANK_ROLE_DEMO: 'Демонстрационное',
    TASK_BANK_ROLE_PRACTICE: 'Для самостоятельной работы',
    TASK_BANK_ROLE_CONTROL: 'Контрольное',
    TASK_BANK_ROLE_REMEDIAL: 'Работа над ошибками',
}

TASK_BANK_ROLE_CHOICES = tuple(TASK_BANK_ROLE_LABELS.items())
TASK_BANK_ROLE_SPECIFIC_CHOICES = tuple(
    (role, label)
    for role, label in TASK_BANK_ROLE_CHOICES
    if role != TASK_BANK_ROLE_ANY
)

TASK_RENDER_MODE_TASK_ONLY = 'task_only'
TASK_RENDER_MODE_WITH_ANSWER = 'with_answer'
TASK_RENDER_MODE_WITH_SHORT_SOLUTION = 'with_short_solution'
TASK_RENDER_MODE_WITH_FULL_SOLUTION = 'with_full_solution'

TASK_RENDER_MODES = frozenset(
    (
        TASK_RENDER_MODE_TASK_ONLY,
        TASK_RENDER_MODE_WITH_ANSWER,
        TASK_RENDER_MODE_WITH_SHORT_SOLUTION,
        TASK_RENDER_MODE_WITH_FULL_SOLUTION,
    )
)

TASK_RENDER_MODE_LABELS = {
    TASK_RENDER_MODE_TASK_ONLY: 'Только задание',
    TASK_RENDER_MODE_WITH_ANSWER: 'Задание + ответ',
    TASK_RENDER_MODE_WITH_SHORT_SOLUTION: 'Задание + краткое решение',
    TASK_RENDER_MODE_WITH_FULL_SOLUTION: 'Задание + полное решение',
}

TASK_RENDER_MODE_CHOICES = tuple(TASK_RENDER_MODE_LABELS.items())

DEFAULT_BLANK_CELLS_ROWS = 6
DEFAULT_BLANK_CELLS_COLUMNS = 24
DEFAULT_BLANK_CELLS_ROW_HEIGHT = 24


def validate_task_bank_role(role: str) -> None:
    if role not in TASK_BANK_ROLES:
        raise ValueError(f'Unsupported task bank role: {role}')


def validate_task_specific_bank_role(role: str) -> None:
    if role not in TASK_BANK_SPECIFIC_ROLES:
        raise ValueError(f'Unsupported specific task bank role: {role}')


def validate_task_render_mode(render_mode: str) -> None:
    if render_mode not in TASK_RENDER_MODES:
        raise ValueError(f'Unsupported task render mode: {render_mode}')
