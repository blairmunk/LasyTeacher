from django.db import models
from django.urls import reverse
from django.core.exceptions import ValidationError
from core.models import BaseModel


def task_image_upload_path(instance, filename):
    """Путь для загрузки изображений заданий"""
    return f'task_images/task_{instance.task.id}/{filename}'


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
                               choices=DIFFICULTY_LEVELS,  # ДОБАВИТЬ choices!
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
    # ИЗМЕНЕНО: убрать default, разрешить пустые значения
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
        # ИЗМЕНЕНО: для пустых позиций возвращаем bottom_70 + специальный класс
        if not self.position:
            return 'task-image-bottom-70 task-image-no-position'
        return css_classes.get(self.position, 'task-image-bottom-70')
    
    @property
    def needs_position(self):
        """True если позиция не задана"""
        return not bool(self.position)
    
    def get_position_status(self):
        """Статус позиции для отчетов"""
        if self.position:
            return f"✅ {self.get_position_display()}"
        else:
            return "⚠️ Позиция не задана"

    @property
    def file_size_human(self):
        """Размер файла в человекочитаемом виде"""
        if self.image and hasattr(self.image, 'size'):
            from django.template.defaultfilters import filesizeformat
            return filesizeformat(self.image.size)
        return "Неизвестно"

    @property  
    def is_image_uploaded(self):
        """True если файл изображения существует"""
        return bool(self.image and hasattr(self.image, 'url'))

    def get_upload_status(self):
        """Статус загрузки для отображения"""
        if self.is_image_uploaded:
            return "✅ Загружено"
        elif self.pk:
            return "⚠️ Не загружено" 
        else:
            return "🆕 Новое"


