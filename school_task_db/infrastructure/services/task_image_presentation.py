"""Presentation values for task images stored by Django."""

from dataclasses import dataclass
from typing import Optional

from django.template.defaultfilters import filesizeformat


@dataclass(frozen=True)
class TaskImageDisplayData:
    has_reference: bool
    has_file: bool
    safe_url: Optional[str]
    file_name: str
    file_size_human: str
    position_status: str


class TaskImagePresentationService:
    CSS_CLASSES = {
        'right_40': 'task-image-right-40',
        'right_20': 'task-image-right-20',
        'bottom_100': 'task-image-bottom-100',
        'bottom_70': 'task-image-bottom-70',
    }
    DEFAULT_CSS_CLASS = 'task-image-bottom-70'

    @classmethod
    def build(cls, task_image) -> TaskImageDisplayData:
        image = task_image.asset.file if task_image.asset_id else None
        has_file = cls.has_file(image)
        return TaskImageDisplayData(
            has_reference=bool(image and image.name),
            has_file=has_file,
            safe_url=cls.safe_url(image),
            file_name=image.name if image else '',
            file_size_human=cls.file_size_human(
                image,
                has_file=has_file,
            ),
            position_status=cls.position_status(
                position=task_image.position,
                position_display=(
                    task_image.get_position_display()
                    if task_image.position
                    else ''
                ),
            ),
        )

    @classmethod
    def css_class(cls, position: str) -> str:
        if not position:
            return f'{cls.DEFAULT_CSS_CLASS} task-image-no-position'
        return cls.CSS_CLASSES.get(position, cls.DEFAULT_CSS_CLASS)

    @staticmethod
    def position_status(position: str, position_display: str) -> str:
        if position:
            return f'✅ {position_display}'
        return '⚠️ Позиция не задана'

    @staticmethod
    def has_file(image) -> bool:
        if not image or not image.name:
            return False
        try:
            return image.storage.exists(image.name)
        except Exception:
            return False

    @staticmethod
    def safe_url(image) -> Optional[str]:
        if not image or not image.name:
            return None
        try:
            return image.url
        except ValueError:
            return None

    @staticmethod
    def file_size_human(image, *, has_file: bool | None = None) -> str:
        if has_file is None:
            has_file = TaskImagePresentationService.has_file(image)
        if not has_file:
            return 'Файл отсутствует'
        try:
            return filesizeformat(image.size)
        except (OSError, ValueError):
            return 'Неизвестно'
