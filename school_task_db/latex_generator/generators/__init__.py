"""Экспорт генераторов"""

from .base import BaseLatexGenerator
from .work_generator import WorkLatexGenerator
from .registry import registry

__all__ = [
    'BaseLatexGenerator',
    'WorkLatexGenerator',
    'registry',
]
