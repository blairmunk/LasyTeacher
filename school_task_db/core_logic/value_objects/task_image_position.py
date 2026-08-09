"""Canonical task image positions and automatic placement hints."""

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


def task_image_position_label(position: str) -> str:
    return TASK_IMAGE_POSITION_LABELS.get(position, position)


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
