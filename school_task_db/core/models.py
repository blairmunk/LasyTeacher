# core/models.py
from django.db import models
import uuid

from core_logic.value_objects.short_uuid import (
    MEDIUM_UUID_LENGTH,
    format_short_uuid,
    is_uuid_search_fragment,
    normalize_uuid_fragment,
    uuid_matches_suffix,
)


class BaseModel(models.Model):
    """Базовая модель с UUID как primary key"""
    # ИЗМЕНЕНО: UUID стал primary key
    id = models.UUIDField('ID', primary_key=True, default=uuid.uuid4, editable=False)
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        abstract = True
    
    def get_short_uuid(self):
        """Возвращает последние 4 символа UUID для отображения"""
        return format_short_uuid(self.id)
    
    def get_medium_uuid(self):
        """Возвращает последние 8 символов UUID"""
        return format_short_uuid(self.id, MEDIUM_UUID_LENGTH)
    
    def get_display_id(self):
        """Красивый ID для отображения пользователю"""
        return f"#{self.get_short_uuid()}"
    
    @classmethod
    def get_by_uuid(cls, uuid_str):
        """Return an exact UUID or one unambiguous suffix match."""
        fragment = normalize_uuid_fragment(uuid_str)
        if not is_uuid_search_fragment(fragment):
            return None

        if len(fragment) == 32:
            try:
                return cls.objects.filter(id=uuid.UUID(fragment)).first()
            except ValueError:
                return None

        matching_ids = [
            object_id
            for object_id in cls.objects.values_list('id', flat=True).iterator()
            if uuid_matches_suffix(object_id, fragment)
        ]
        if len(matching_ids) == 1:
            return cls.objects.filter(id=matching_ids[0]).first()
        return None
    
    # НОВОЕ: удобные методы для совместимости
    @property
    def uuid(self):
        """Алиас для совместимости со старым кодом"""
        return self.id
    
    @property
    def pk(self):
        """Primary key - теперь UUID"""
        return self.id


class BaseModelWithOrder(BaseModel):
    """Базовая модель с полем порядка"""
    order = models.PositiveIntegerField('Порядок', default=1)
    
    class Meta:
        abstract = True
        ordering = ['order', 'created_at']

class AcademicYear(BaseModel):
    """Учебный год"""
    name = models.CharField(
        'Название', max_length=20, unique=True,
        help_text='Например: 2025-2026'
    )
    start_date = models.DateField('Начало')
    end_date = models.DateField('Окончание')
    is_active = models.BooleanField(
        'Текущий год', default=False,
        help_text='Только один год может быть активным'
    )

    class Meta:
        verbose_name = 'Учебный год'
        verbose_name_plural = 'Учебные годы'
        ordering = ['-start_date']
        constraints = [
            models.UniqueConstraint(
                fields=['is_active'],
                condition=models.Q(is_active=True),
                name='unique_active_academic_year',
            ),
        ]

    def __str__(self):
        return self.name

class ImportLog(BaseModel):
    """Лог операции импорта заданий"""
    
    class Mode(models.TextChoices):
        STRICT = 'strict', 'Строгий'
        UPDATE = 'update', 'Обновление'
        SKIP = 'skip', 'Пропуск дубликатов'
    
    class Status(models.TextChoices):
        VALIDATING = 'validating', 'Валидация'
        IMPORTING = 'importing', 'Импорт'
        SUCCESS = 'success', 'Успешно'
        PARTIAL = 'partial', 'Частично'
        FAILED = 'failed', 'Ошибка'
    
    filename = models.CharField('Имя файла', max_length=255)
    mode = models.CharField(
        'Режим', max_length=10,
        choices=Mode.choices, default=Mode.UPDATE
    )
    dry_run = models.BooleanField('Пробный запуск', default=False)
    
    # Статистика
    tasks_created = models.PositiveIntegerField('Заданий создано', default=0)
    tasks_updated = models.PositiveIntegerField('Заданий обновлено', default=0)
    tasks_skipped = models.PositiveIntegerField('Заданий пропущено', default=0)
    groups_created = models.PositiveIntegerField('Групп создано', default=0)
    topics_created = models.PositiveIntegerField('Тем создано', default=0)
    images_created = models.PositiveIntegerField('Изображений создано', default=0)
    errors_count = models.PositiveIntegerField('Количество ошибок', default=0)
    
    # Детали
    details = models.JSONField('Детальный отчёт', default=dict, blank=True)
    error_messages = models.JSONField('Ошибки', default=list, blank=True)
    
    # Метаданные
    status = models.CharField(
        'Статус', max_length=20,
        choices=Status.choices, default=Status.VALIDATING
    )
    file_size = models.PositiveIntegerField('Размер файла (байт)', default=0)
    duration_ms = models.PositiveIntegerField('Длительность (мс)', default=0)
    
    class Meta:
        verbose_name = 'Лог импорта'
        verbose_name_plural = 'Логи импорта'
        ordering = ['-created_at']
    
    def __str__(self):
        return (
            f'{self.filename} — {self.get_status_display()} '
            f'({self.created_at:%d.%m.%Y %H:%M})'
        )
