from pathlib import Path

from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from core.models import BaseModel
from core_logic.value_objects.task_validation import (
    validate_task_topic_selection,
)
from core_logic.value_objects.task_image_position import (
    TASK_IMAGE_POSITION_CHOICES,
)


def task_image_upload_path(instance, filename):
    """Compatibility path retained for historical Django migrations."""
    return f'task_images/task_{instance.task.id}/{filename}'


def image_asset_upload_path(instance, filename):
    """Store immutable assets under a checksum-derived path."""
    extension = Path(filename).suffix.lower()[:16]
    checksum = instance.checksum or str(instance.pk)
    return f'image_assets/{checksum[:2]}/{checksum}{extension}'


class Source(BaseModel):
    """Источник задания — книга, сайт, сборник"""
    SOURCE_TYPE_CHOICES = [
        ('textbook', 'Учебник'),
        ('problem_book', 'Задачник'),
        ('exam', 'ЕГЭ/ОГЭ'),
        ('olympiad', 'Олимпиада'),
        ('website', 'Сайт'),
        ('original', 'Авторское'),
        ('other', 'Другое'),
    ]

    name = models.CharField('Название', max_length=300,
                             help_text='Например: Перышкин А.В. Физика. 8 класс')
    short_name = models.CharField('Краткое название', max_length=100, blank=True,
                                   help_text='Например: Перышкин-8')
    source_type = models.CharField('Тип источника', max_length=50,
                                    choices=SOURCE_TYPE_CHOICES, default='textbook')
    author = models.CharField('Автор', max_length=200, blank=True)
    year = models.PositiveIntegerField('Год издания', null=True, blank=True)
    url = models.URLField('Ссылка', blank=True,
                           help_text='URL сайта или онлайн-ресурса')
    isbn = models.CharField('ISBN', max_length=20, blank=True)
    notes = models.TextField('Примечания', blank=True)

    class Meta:
        verbose_name = 'Источник'
        verbose_name_plural = 'Источники'
        ordering = ['name']

    def __str__(self):
        if self.short_name:
            return self.short_name
        return self.name

class Task(BaseModel):
    """Задание"""
    TASK_TYPES = [
        ('qualitative', 'Качественная задача'),
        ('computational', 'Расчётная задача'),
        ('theoretical', 'Теоретический вопрос'),
        ('practical', 'Практическое задание'),
        ('test', 'Тестовое задание'),
    ]
    
    DIFFICULTY_LEVELS = [
        (1, 'Начальный'),
        (2, 'Базовый'),
        (3, 'Базовый+'),
        (4, 'Повышенный'),
        (5, 'Высокий'),
        (6, 'Олимпиадный'),
    ]
    
    # Основное содержание
    text = models.TextField('Текст задания')
    answer = models.TextField('Ответ')
    short_solution = models.TextField('Краткое решение', blank=True)
    full_solution = models.TextField('Полное решение', blank=True)
    hint = models.TextField('Подсказка', blank=True)
    instruction = models.TextField('Инструкция к выполнению', blank=True)
    
    # ОБНОВЛЕННЫЕ СВЯЗИ:
    topic = models.ForeignKey('curriculum.Topic', on_delete=models.PROTECT, 
                             verbose_name='Основная тема')
    subtopic = models.ForeignKey('curriculum.SubTopic', on_delete=models.SET_NULL,
                               null=True, blank=True, 
                               verbose_name='Подтема')
    
    # Характеристики
    task_type = models.CharField('Тип задания', max_length=20, choices=TASK_TYPES)
    difficulty = models.IntegerField('Сложность', 
                               choices=DIFFICULTY_LEVELS,  
                               help_text='Уровень сложности задания')
    
    # Дополнительные поля
    cognitive_level = models.CharField('Уровень познания', max_length=20, choices=[
        ('remember', 'Запоминание'),
        ('understand', 'Понимание'), 
        ('apply', 'Применение'),
        ('analyze', 'Анализ'),
        ('evaluate', 'Оценка'),
        ('create', 'Создание')
    ], default='understand')
    
    estimated_time = models.PositiveIntegerField('Время выполнения (мин)', null=True, blank=True)

    # === Источник ===
    source = models.ForeignKey(
        'Source', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Источник',
        help_text='Книга, сайт, сборник, откуда взято задание'
    )
    source_detail = models.CharField(
        'Детали источника', max_length=200, blank=True,
        help_text='Стр. 45, №12 / Вариант 3, задание 5'
    )

    # === Метаданные ===
    grade = models.PositiveIntegerField(
        'Класс', null=True, blank=True,
        help_text='Рекомендуемый класс (7–11)',
        choices=[(i, f'{i} класс') for i in range(7, 12)]
    )
    year = models.PositiveIntegerField(
        'Год задания', null=True, blank=True,
        help_text='Год составления/публикации (ЕГЭ 2024, олимпиада 2023)'
    )

    # === Качество ===
    is_verified = models.BooleanField(
        'Проверено', default=False,
        help_text='Задание вычитано, ответ проверен'
    )
    teacher_notes = models.TextField(
        'Заметки учителя', blank=True,
        help_text='Личные пометки: особенности, типичные ошибки учеников'
    )
    
    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.topic.name} - {self.text[:50]}..."
    
    def get_absolute_url(self):
        return reverse('tasks:detail', kwargs={'pk': self.pk})
    
    def clean(self):
        errors = validate_task_topic_selection(
            topic_id=str(self.topic_id or ''),
            subtopic_id=str(self.subtopic_id or ''),
            subtopic_topic_id=(
                str(self.subtopic.topic_id)
                if self.subtopic_id
                else None
            ),
        )
        if errors:
            raise ValidationError(errors)

class ImageAsset(BaseModel):
    """Immutable binary image content shared by task-image references."""

    file = models.FileField('Файл', upload_to=image_asset_upload_path)
    checksum = models.CharField(
        'SHA-256',
        max_length=64,
        unique=True,
        editable=False,
    )
    byte_size = models.PositiveBigIntegerField('Размер, байт', editable=False)
    mime_type = models.CharField(
        'MIME-тип',
        max_length=100,
        blank=True,
        editable=False,
    )
    original_filename = models.CharField(
        'Исходное имя файла',
        max_length=255,
        blank=True,
        editable=False,
    )

    class Meta:
        verbose_name = 'Неизменяемый файл изображения'
        verbose_name_plural = 'Неизменяемые файлы изображений'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('ImageAsset является неизменяемым')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            'ImageAsset может использоваться историческими снимками',
        )

    def __str__(self):
        return f'{self.original_filename or "Изображение"} [{self.checksum[:12]}]'


class TaskImage(BaseModel):
    """Изображение для задания"""
    POSITION_CHOICES = TASK_IMAGE_POSITION_CHOICES
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images', verbose_name='Задание')
    asset = models.ForeignKey(
        ImageAsset,
        on_delete=models.PROTECT,
        related_name='task_references',
        null=True,
        blank=True,
        verbose_name='Файл изображения',
        help_text='Пусто только у старых записей с потерянным файлом',
    )
    position = models.CharField('Расположение', max_length=20, choices=POSITION_CHOICES, 
                               blank=True, help_text='Оставьте пустым для установки позже')
    caption = models.CharField('Подпись к изображению', max_length=200, blank=True)
    order = models.PositiveIntegerField('Порядок отображения', default=1)
    
    class Meta:
        verbose_name = 'Изображение задания'
        verbose_name_plural = 'Изображения заданий'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        position_display = self.get_position_display() if self.position else 'Позиция не задана'
        return f"Изображение для {self.task.topic.name} ({position_display})"

    @property
    def image(self):
        """Compatibility read accessor for presentation and form templates."""
        return self.asset.file if self.asset_id else None
