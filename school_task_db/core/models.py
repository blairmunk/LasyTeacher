# core/models.py
from django.db import models
import uuid


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
        return str(self.id)[-4:].upper()
    
    def get_medium_uuid(self):
        """Возвращает последние 8 символов UUID"""
        return str(self.id)[-8:].upper()
    
    def get_display_id(self):
        """Красивый ID для отображения пользователю"""
        return f"#{self.get_short_uuid()}"
    
    @classmethod
    def get_by_uuid(cls, uuid_str):
        """УПРОЩЕНО: теперь UUID = primary key"""
        try:
            if len(uuid_str) == 36:
                # Полный UUID
                return cls.objects.get(id=uuid_str)  # id теперь UUID
            elif len(uuid_str) >= 3:
                # Поиск по окончанию UUID
                uuid_str = uuid_str.lower().replace('#', '')
                matches = cls.objects.filter(id__iendswith=uuid_str)
                return matches.first() if matches.count() == 1 else None
        except (cls.DoesNotExist, ValueError):
            pass
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
    
    @property
    def total_processed(self):
        """Общее количество обработанных заданий"""
        return self.tasks_created + self.tasks_updated + self.tasks_skipped
    
    @property
    def status_icon(self):
        """Иконка статуса для отображения"""
        icons = {
            self.Status.VALIDATING: '🔍',
            self.Status.IMPORTING: '⏳',
            self.Status.SUCCESS: '✅',
            self.Status.PARTIAL: '⚠️',
            self.Status.FAILED: '❌',
        }
        return icons.get(self.status, '❓')
    
    @property
    def duration_human(self):
        """Длительность в человекочитаемом виде"""
        if self.duration_ms < 1000:
            return f'{self.duration_ms} мс'
        return f'{self.duration_ms / 1000:.1f} с'
    
    @property
    def file_size_human(self):
        """Размер файла в человекочитаемом виде"""
        if self.file_size < 1024:
            return f'{self.file_size} Б'
        if self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f} КБ'
        return f'{self.file_size / 1024 / 1024:.1f} МБ'
