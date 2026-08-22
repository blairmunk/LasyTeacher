"""Canonical task image positions and document layout hints."""

from dataclasses import dataclass

TASK_IMAGE_POSITION_RIGHT_40 = 'right_40'
TASK_IMAGE_POSITION_RIGHT_20 = 'right_20'
TASK_IMAGE_POSITION_BOTTOM_100 = 'bottom_100'
TASK_IMAGE_POSITION_BOTTOM_70 = 'bottom_70'

TASK_IMAGE_POSITION_LABELS = {
    TASK_IMAGE_POSITION_RIGHT_40: 'Справа 40% (обтекание текстом 60%)',
    TASK_IMAGE_POSITION_RIGHT_20: 'Справа 20% (обтекание текстом 80%)',
    TASK_IMAGE_POSITION_BOTTOM_100: 'Снизу по центру 100% ширины',
    TASK_IMAGE_POSITION_BOTTOM_70: 'Снизу по центру 70% ширины',
}
TASK_IMAGE_POSITION_CHOICES = tuple(TASK_IMAGE_POSITION_LABELS.items())


@dataclass(frozen=True)
class TaskImageLayout:
    placement: str
    width_percent: int


TASK_IMAGE_LAYOUTS = {
    TASK_IMAGE_POSITION_RIGHT_40: TaskImageLayout(
        placement='right',
        width_percent=40,
    ),
    TASK_IMAGE_POSITION_RIGHT_20: TaskImageLayout(
        placement='right',
        width_percent=20,
    ),
    TASK_IMAGE_POSITION_BOTTOM_100: TaskImageLayout(
        placement='bottom',
        width_percent=100,
    ),
    TASK_IMAGE_POSITION_BOTTOM_70: TaskImageLayout(
        placement='bottom',
        width_percent=70,
    ),
}
DEFAULT_TASK_IMAGE_LAYOUT = TASK_IMAGE_LAYOUTS[TASK_IMAGE_POSITION_BOTTOM_70]


def task_image_position_label(position: str) -> str:
    return TASK_IMAGE_POSITION_LABELS.get(position, position)


def task_image_layout(position: str) -> TaskImageLayout:
    return TASK_IMAGE_LAYOUTS.get(position, DEFAULT_TASK_IMAGE_LAYOUT)


def suggest_task_image_position(caption: str) -> str:
    normalized_caption = (caption or '').lower()
    if 'таблица' in normalized_caption:
        return TASK_IMAGE_POSITION_BOTTOM_100
    if any(
        word in normalized_caption
        for word in ('портрет', 'фото', 'изображение')
    ):
        return TASK_IMAGE_POSITION_RIGHT_20
    return TASK_IMAGE_POSITION_BOTTOM_70
