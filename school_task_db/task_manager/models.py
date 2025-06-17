from django.db import models
from django.urls import reverse
import json
import random
import os


def task_image_upload_path(instance, filename):
    """Путь для загрузки изображений заданий"""
    return f'task_images/task_{instance.task.id}/{filename}'


class AnalogGroup(models.Model):
    """Группа аналогичных заданий"""
    name = models.CharField('Название группы', max_length=200)
    description = models.TextField('Описание', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Группа аналогичных заданий'
        verbose_name_plural = 'Группы аналогичных заданий'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_sample_task(self):
        """Возвращает одно задание из группы для предварительного просмотра"""
        return self.tasks.first()


class Task(models.Model):
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
    
    # Связи
    analog_groups = models.ManyToManyField(AnalogGroup, related_name='tasks', blank=True, verbose_name='Группы аналогов')
    
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)
    
    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.topic} - {self.text[:50]}..."
    
    def get_absolute_url(self):
        return reverse('task_manager:task-detail', kwargs={'pk': self.pk})


class TaskImage(models.Model):
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
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
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


# Остальные модели остаются без изменений...
class Work(models.Model):
    """Работа"""
    name = models.CharField('Название работы', max_length=200)
    duration = models.PositiveIntegerField('Время выполнения (минуты)', default=45)
    variant_counter = models.PositiveIntegerField('Счётчик вариантов', default=0)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Работа'
        verbose_name_plural = 'Работы'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('task_manager:work-detail', kwargs={'pk': self.pk})
    
    def generate_variants(self, count=1):
        """Генерация вариантов на основе работы"""
        variants = []
        for i in range(count):
            self.variant_counter += 1
            variant = Variant.objects.create(
                work=self,
                number=self.variant_counter
            )
            
            # Добавляем задания в вариант
            for work_group in self.workanaloggroup_set.all():
                # Получаем случайные задания из группы
                available_tasks = list(work_group.analog_group.tasks.all())
                if len(available_tasks) >= work_group.count:
                    selected_tasks = random.sample(available_tasks, work_group.count)
                    variant.tasks.add(*selected_tasks)
            
            variants.append(variant)
        
        self.save()
        return variants


class WorkAnalogGroup(models.Model):
    """Связь работы с группой аналогов и количеством заданий"""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    analog_group = models.ForeignKey(AnalogGroup, on_delete=models.CASCADE, verbose_name='Группа аналогов')
    count = models.PositiveIntegerField('Количество заданий', default=1)
    
    class Meta:
        verbose_name = 'Группа заданий в работе'
        verbose_name_plural = 'Группы заданий в работе'
        unique_together = ['work', 'analog_group']
    
    def __str__(self):
        return f"{self.work.name} - {self.analog_group.name} ({self.count})"


class Variant(models.Model):
    """Вариант работы"""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    number = models.PositiveIntegerField('Номер варианта')
    tasks = models.ManyToManyField(Task, verbose_name='Задания')
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Вариант'
        verbose_name_plural = 'Варианты'
        ordering = ['work', 'number']
        unique_together = ['work', 'number']
    
    def __str__(self):
        return f"{self.work.name} - Вариант {self.number}"
    
    def get_absolute_url(self):
        return reverse('task_manager:variant-detail', kwargs={'pk': self.pk})


class Student(models.Model):
    """Ученик"""
    first_name = models.CharField('Имя', max_length=100)
    last_name = models.CharField('Фамилия', max_length=100)
    middle_name = models.CharField('Отчество', max_length=100, blank=True)
    email = models.EmailField('Email', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Ученик'
        verbose_name_plural = 'Ученики'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.last_name} {self.first_name}"
    
    def get_full_name(self):
        parts = [self.last_name, self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        return ' '.join(parts)


class StudentGroup(models.Model):
    """Класс"""
    name = models.CharField('Название класса', max_length=100)
    students = models.ManyToManyField(Student, verbose_name='Ученики', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Класс'
        verbose_name_plural = 'Классы'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Event(models.Model):
    """Событие (проведение работы)"""
    STATUS_CHOICES = [
        ('planned', 'Запланировано'),
        ('conducted', 'Проведено'),
        ('checked', 'Проверено'),
        ('graded', 'Оценено'),
        ('closed', 'Закрыто'),
    ]
    
    name = models.CharField('Название события', max_length=200)
    date = models.DateTimeField('Дата проведения')
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    student_group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, verbose_name='Класс')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='planned')
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.name} - {self.student_group.name}"
    
    def get_absolute_url(self):
        return reverse('task_manager:event-detail', kwargs={'pk': self.pk})


class Mark(models.Model):
    """Отметка"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, verbose_name='Ученик')
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, verbose_name='Вариант')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name='Событие', null=True, blank=True)
    score = models.PositiveIntegerField('Оценка', null=True, blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    
    class Meta:
        verbose_name = 'Отметка'
        verbose_name_plural = 'Отметки'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student} - {self.variant} - {self.score or 'Не оценено'}"
        