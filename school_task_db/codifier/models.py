from django.db import models
from django.urls import reverse
from core.models import BaseModel


class CodifierSpec(BaseModel):
    """
    Спецификация кодификатора.
    Примеры: ОГЭ 2026 Физика, ЕГЭ 2026 Физика
    """
    name = models.CharField('Полное название', max_length=200)
    short_name = models.CharField('Краткое название', max_length=30,
        help_text='Например: ОГЭ 2026')
    subject = models.CharField('Предмет', max_length=100, default='Физика')
    exam_type = models.CharField('Тип экзамена', max_length=20, choices=[
        ('oge', 'ОГЭ'),
        ('ege', 'ЕГЭ'),
        ('vpr', 'ВПР'),
        ('custom', 'Авторский'),
    ])
    year = models.IntegerField('Год')
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Кодификатор'
        verbose_name_plural = 'Кодификаторы'
        ordering = ['-year', 'exam_type']
        unique_together = ['exam_type', 'year', 'subject']

    def __str__(self):
        return self.short_name

    def get_absolute_url(self):
        return reverse('codifier:spec-detail', kwargs={'pk': self.pk})


class ContentEntry(BaseModel):
    """
    Элемент содержания кодификатора.

    ОГЭ:  code="1" name="Механические явления"  (раздел, parent=None)
          code="1.4" name="Равноускоренное..."    (элемент, parent=раздел)

    ЕГЭ:  code="1" name="Механика"               (раздел)
          code="1.1" name="Кинематика"            (подраздел)
          code="1.1.6" name="Равноускоренное..."   (элемент)
    """
    codifier = models.ForeignKey(
        CodifierSpec, on_delete=models.CASCADE,
        related_name='content_entries',
        verbose_name='Кодификатор',
    )
    code = models.CharField('Код', max_length=20,
        help_text='Например: 1.4, 1.1.6, 3.2.3')
    name = models.CharField('Формулировка', max_length=500)

    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='children',
        verbose_name='Родительский элемент',
    )

    # Привязка к curriculum: topic обязателен, subtopic — для точной привязки
    topic = models.ForeignKey(
        'curriculum.Topic', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='codifier_entries',
        verbose_name='Тема',
        help_text='Общая тема (Кинематика, Динамика...)',
    )
    subtopic = models.ForeignKey(
        'curriculum.SubTopic', on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='codifier_entries',
        verbose_name='Подтема',
        help_text='Конкретный элемент (Равноускоренное движение...)',
    )

    # Доп. поля из документов ФИПИ
    grade_studied = models.CharField(
        'Класс изучения', max_length=20, blank=True,
        help_text='7, 8, 9 или 7, 9')

    class Meta:
        verbose_name = 'Элемент содержания'
        verbose_name_plural = 'Элементы содержания'
        ordering = ['codifier', 'code']
        unique_together = ['codifier', 'code']

    def __str__(self):
        return f'{self.codifier.short_name} {self.code} {self.name[:60]}'



class Requirement(BaseModel):
    """
    Предметное требование к уровню подготовки.
    Из раздела 1 кодификатора (только предметные).

    Примеры:
    ОГЭ: 1 "Знать/понимать смысл понятий: физическое явление..."
    ЕГЭ: 1 "Знать/понимать смысл физических понятий..."
    """
    codifier = models.ForeignKey(
        CodifierSpec, on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name='Кодификатор',
    )
    code = models.CharField('Код', max_length=20)
    name = models.TextField('Формулировка')

    cognitive_level = models.CharField(
        'Когнитивный уровень', max_length=20,
        blank=True,
        choices=[
            ('know', 'Знать / понимать'),
            ('apply', 'Уметь'),
            ('use', 'Использовать на практике'),
        ],
    )

    # M2M к заданиям (прямая связь: какие задания проверяют это требование)
    tasks = models.ManyToManyField(
        'tasks.Task', blank=True,
        related_name='codifier_requirements',
        verbose_name='Задания',
    )

    class Meta:
        verbose_name = 'Требование'
        verbose_name_plural = 'Требования'
        ordering = ['codifier', 'code']
        unique_together = ['codifier', 'code']

    def __str__(self):
        return f'{self.codifier.short_name} Тр.{self.code} {self.name[:60]}'
