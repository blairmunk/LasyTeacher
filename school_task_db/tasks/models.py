from django.db import models
from django.urls import reverse
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
    
    text = models.TextField('Текст задания')
    answer = models.TextField('Ответ')
    short_solution = models.TextField('Краткое решение', blank=True)
    full_solution = models.TextField('Полное решение', blank=True)
    hint = models.TextField('Подсказка', blank=True)
    instruction = models.TextField('Инструкция к выполнению', blank=True)
    
    # Тематическая структура
    section = models.CharField('Тематический раздел', max_length=200)
    topic = models.CharField('Тема', max_length=200)
    subtopic = models.CharField('Подтема', max_length=200, blank=True)
    
    # Кодификатор
    content_element = models.CharField('Элемент содержания', max_length=100, blank=True)
    requirement_element = models.CharField('Элемент требований', max_length=100, blank=True)
    
    # Характеристики
    task_type = models.CharField('Тип задания', max_length=20, choices=TASK_TYPES)
    difficulty = models.IntegerField('Сложность', choices=DIFFICULTY_LEVELS)
    
    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.topic} - {self.text[:50]}..."
    
    def get_absolute_url(self):
        return reverse('tasks:detail', kwargs={'pk': self.pk})

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
    position = models.CharField('Расположение', max_length=20, choices=POSITION_CHOICES, default='bottom_70')
    caption = models.CharField('Подпись к изображению', max_length=200, blank=True)
    order = models.PositiveIntegerField('Порядок отображения', default=1)
    
    class Meta:
        verbose_name = 'Изображение задания'
        verbose_name_plural = 'Изображения заданий'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"Изображение для {self.task.topic} ({self.get_position_display()})"
    
    def get_css_class(self):
        """Возвращает CSS класс для позиционирования изображения"""
        css_classes = {
            'right_40': 'task-image-right-40',
            'right_20': 'task-image-right-20',
            'bottom_100': 'task-image-bottom-100',
            'bottom_70': 'task-image-bottom-70',
        }
        return css_classes.get(self.position, 'task-image-bottom-70')
