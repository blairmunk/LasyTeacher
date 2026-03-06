from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from core.models import BaseModel


def task_image_upload_path(instance, filename):
    """Путь для загрузки изображений заданий"""
    return f'task_images/task_{instance.task.id}/{filename}'


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

    @property
    def display_name(self):
        parts = []
        if self.author:
            parts.append(self.author)
        parts.append(self.name)
        if self.year:
            parts.append(f'({self.year})')
        return ' — '.join(parts) if len(parts) > 1 else parts[0]


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
        (1, 'Подготовительный'),
        (2, 'Базовый'),
        (3, 'Повышенный'),
        (4, 'Высокий'),
        (5, 'Экспертный'),
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
    
    # Кодификатор
    content_element = models.CharField('Элемент содержания', max_length=100, blank=True)
    requirement_element = models.CharField('Элемент требований', max_length=100, blank=True)
    
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
        """Валидация: подтема должна принадлежать выбранной теме"""
        if self.subtopic and self.topic:
            if self.subtopic.topic != self.topic:
                raise ValidationError('Подтема должна принадлежать выбранной основной теме')

    def save(self, *args, **kwargs):
        """Переопределенное сохранение для отслеживания изменений текста"""
        # Проверяем изменился ли текст задания
        if self.pk:
            try:
                old_instance = Task.objects.get(pk=self.pk)
                if old_instance.text != self.text:
                    self._text_changed = True
            except Task.DoesNotExist:
                pass
        
        super().save(*args, **kwargs)
    
    # Свойства для удобства
    @property
    def subject(self):
        """Предмет через тему"""
        return self.topic.subject if self.topic else None
    
    @property
    def grade_level(self):
        """Класс через тему"""
        return self.topic.grade_level if self.topic else None
    
    @property
    def section(self):
        """Раздел через тему"""
        return self.topic.section if self.topic else None
    
    def get_full_topic_path(self):
        """Полный путь темы для отображения"""
        if self.subtopic:
            return f"{self.topic.name} → {self.subtopic.name}"
        return self.topic.name

class TaskImage(BaseModel):
    """Изображение для задания"""
    POSITION_CHOICES = [
        ('right_40', 'Справа 40% (обтекание текстом 60%)'),
        ('right_20', 'Справа 20% (обтекание текстом 80%)'),
        ('bottom_100', 'Снизу по центру 100% ширины'),
        ('bottom_70', 'Снизу по центру 70% ширины'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images', verbose_name='Задание')
    image = models.ImageField('Изображение', upload_to=task_image_upload_path)
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
    
    def get_css_class(self):
        """Возвращает CSS класс для позиционирования изображения"""
        css_classes = {
            'right_40': 'task-image-right-40',
            'right_20': 'task-image-right-20', 
            'bottom_100': 'task-image-bottom-100',
            'bottom_70': 'task-image-bottom-70',
        }
        if not self.position:
            return 'task-image-bottom-70 task-image-no-position'
        return css_classes.get(self.position, 'task-image-bottom-70')
    
    @property
    def needs_position(self):
        """True если позиция не задана"""
        return not bool(self.position)
    
    def get_position_status(self):
        """Статус позиции для отчётов"""
        if self.position:
            return f"✅ {self.get_position_display()}"
        else:
            return "⚠️ Позиция не задана"

    # ===== ИСПРАВЛЕННЫЕ СВОЙСТВА =====

    @property
    def has_file(self):
        """Проверяет, что файл реально существует на диске"""
        if not self.image:
            return False
        if not self.image.name:
            return False
        try:
            return self.image.storage.exists(self.image.name)
        except Exception:
            return False

    @property
    def safe_url(self):
        """Безопасное получение URL — возвращает None вместо ValueError"""
        if not self.image:
            return None
        if not self.image.name:
            return None
        try:
            return self.image.url
        except ValueError:
            return None

    @property  
    def is_image_uploaded(self):
        """True если файл изображения существует — ИСПРАВЛЕНО"""
        return self.has_file

    @property
    def file_size_human(self):
        """Размер файла в человекочитаемом виде"""
        if not self.has_file:
            return "Файл отсутствует"
        try:
            from django.template.defaultfilters import filesizeformat
            return filesizeformat(self.image.size)
        except (OSError, ValueError):
            return "Неизвестно"

    def get_upload_status(self):
        """Статус загрузки для отображения"""
        if self.has_file:
            return "✅ Загружено"
        elif self.image.name:
            return "❌ Файл не найден на диске"
        elif self.pk:
            return "⚠️ Не загружено" 
        else:
            return "🆕 Новое"


