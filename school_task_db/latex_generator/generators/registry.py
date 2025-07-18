"""Реестр генераторов LaTeX"""

from typing import Dict, Type
from .base import BaseLatexGenerator
from .work_generator import WorkLatexGenerator

class GeneratorRegistry:
    """Реестр всех доступных генераторов"""
    
    _generators: Dict[str, Type[BaseLatexGenerator]] = {
        'work': WorkLatexGenerator,
        # В будущем добавим:
        # 'report': ReportLatexGenerator,
        # 'certificate': CertificateLatexGenerator,
    }
    
    @classmethod
    def get_generator(cls, generator_type: str) -> Type[BaseLatexGenerator]:
        """Получить класс генератора по типу"""
        if generator_type not in cls._generators:
            available = ', '.join(cls._generators.keys())
            raise ValueError(f"Неизвестный тип генератора: {generator_type}. Доступные: {available}")
        
        return cls._generators[generator_type]
    
    @classmethod
    def get_available_types(cls) -> list:
        """Получить список доступных типов генераторов"""
        return list(cls._generators.keys())
    
    @classmethod
    def register_generator(cls, generator_type: str, generator_class: Type[BaseLatexGenerator]):
        """Зарегистрировать новый генератор"""
        cls._generators[generator_type] = generator_class

# Экземпляр для использования
registry = GeneratorRegistry()
