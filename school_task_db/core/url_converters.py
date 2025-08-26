"""
Универсальные URL конвертеры для поддержки UUID
"""
import uuid
from django.urls.converters import UUIDConverter

class UniversalUUIDConverter(UUIDConverter):
    """
    Конвертер который поддерживает UUID в любом контексте
    Работает как стандартный UUIDConverter, но более гибкий
    """
    regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    
    def to_python(self, value):
        try:
            return uuid.UUID(value)
        except ValueError:
            raise ValueError("Invalid UUID format")
    
    def to_url(self, value):
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

class FlexibleUUIDConverter:
    """
    Гибкий конвертер который поддерживает и int и UUID
    Для обратной совместимости (если понадобится)
    """
    regex = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}|[0-9]+'
    
    def to_python(self, value):
        # Сначала пробуем UUID
        if len(value) == 36 and '-' in value:
            try:
                return uuid.UUID(value)
            except ValueError:
                pass
        
        # Затем пробуем int (для обратной совместимости)
        try:
            return int(value)
        except ValueError:
            raise ValueError("Invalid UUID or int format")
    
    def to_url(self, value):
        return str(value)
