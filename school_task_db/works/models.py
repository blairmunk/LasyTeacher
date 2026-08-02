from django.db import models
from django.urls import reverse

from core.models import BaseModel
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_ROWS,
    TASK_BANK_ROLE_ANY,
    TASK_BANK_ROLE_CHOICES,
    TASK_BANK_ROLE_CONTROL,
    TASK_BANK_ROLE_SPECIFIC_CHOICES,
    TASK_RENDER_MODE_CHOICES,
    TASK_RENDER_MODE_TASK_ONLY,
)
from core_logic.value_objects.work_content_plan import (
    WORK_CONTENT_TEXT,
    WORK_CONTENT_THEORY,
)


class Work(BaseModel):
    """Работа — мутабельный шаблон"""
    WORK_TYPE_CHOICES = [
        ('test', 'Контрольная работа'),
        ('quiz', 'Самостоятельная работа'),
        ('exam', 'Экзамен'),
        ('diagnostic', 'Диагностическая работа'),
        ('homework', 'Домашняя работа'),
        ('practice', 'Практическая работа'),
        ('remedial', 'Работа над ошибками'),
        ('individual', 'Индивидуальная работа'),
    ]


    name = models.CharField('Название работы', max_length=200)
    duration = models.PositiveIntegerField('Время выполнения (минуты)', default=45)
    variant_counter = models.PositiveIntegerField('Счётчик вариантов', default=0)
    work_type = models.CharField('Тип работы', max_length=50,
                                 choices=WORK_TYPE_CHOICES, default='test')
    max_score = models.PositiveIntegerField(
        'Максимальный балл', default=0,
        help_text='Шкала нормировки. 0 = сумма весов (без нормировки)'
    )

    class Meta:
        verbose_name = 'Работа'
        verbose_name_plural = 'Работы'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_short_uuid()}] {self.name}"

    def get_absolute_url(self):
        return reverse('works:detail', kwargs={'pk': self.pk})

class WorkAnalogGroup(BaseModel):
    """Спецификация работы: группа аналогов + количество + вес"""
    work = models.ForeignKey(Work, on_delete=models.CASCADE, verbose_name='Работа')
    analog_group = models.ForeignKey('task_groups.AnalogGroup',
                                     on_delete=models.CASCADE,
                                     verbose_name='Группа аналогов')
    count = models.PositiveIntegerField('Количество заданий', default=1)
    order = models.PositiveIntegerField('Порядок в работе', default=0)
    weight = models.PositiveIntegerField('Вес задания', default=1,
                                          help_text='Вес для нормировки баллов')
    bank_role_filter = models.CharField(
        'Роль заданий',
        max_length=20,
        choices=TASK_BANK_ROLE_CHOICES,
        default=TASK_BANK_ROLE_ANY,
        help_text='Какие задания выбирать из группы аналогов',
    )
    render_mode = models.CharField(
        'Режим печати',
        max_length=40,
        choices=TASK_RENDER_MODE_CHOICES,
        default=TASK_RENDER_MODE_TASK_ONLY,
    )
    is_assessable = models.BooleanField('Оценивать', default=True)
    blank_cells_after = models.BooleanField(
        'Пустые клетки после задания',
        default=False,
    )
    blank_cells_rows = models.PositiveIntegerField(
        'Строк клеток',
        default=DEFAULT_BLANK_CELLS_ROWS,
    )

    class Meta:
        verbose_name = 'Группа заданий в работе'
        verbose_name_plural = 'Группы заданий в работе'
        ordering = ['order', 'pk']

    def __str__(self):
        return (
            f"{self.work.name} — #{self.order} {self.analog_group.name} "
            f"(×{self.count}, вес={self.weight})"
        )


class WorkContentBlock(BaseModel):
    """Постоянный содержательный блок в педагогическом плане работы."""

    CONTENT_TYPE_CHOICES = [
        (WORK_CONTENT_THEORY, 'Теория'),
        (WORK_CONTENT_TEXT, 'Текст'),
    ]

    work = models.ForeignKey(
        Work,
        on_delete=models.CASCADE,
        related_name='content_blocks',
        verbose_name='Работа',
    )
    content_type = models.CharField(
        'Тип содержимого',
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
    )
    order = models.PositiveIntegerField('Порядок в работе', default=0)
    title = models.CharField('Заголовок', max_length=200, blank=True)
    body = models.TextField(
        'Текст',
        blank=True,
        help_text='Произвольный текст для текстового блока.',
    )
    topics = models.ManyToManyField(
        'curriculum.Topic',
        blank=True,
        related_name='work_content_blocks',
        verbose_name='Темы',
        help_text='Источники содержания для теоретического блока.',
    )
    include_subtopics = models.BooleanField(
        'Включать подтемы',
        default=False,
    )

    class Meta:
        verbose_name = 'Содержательный блок работы'
        verbose_name_plural = 'Содержательные блоки работы'
        ordering = ['order', 'pk']

    def __str__(self):
        title = self.title or self.get_content_type_display()
        return f'{self.work.name} — #{self.order} {title}'


class Variant(BaseModel):
    """Вариант работы — иммутабельный набор заданий с баллами"""
    work = models.ForeignKey(Work, on_delete=models.SET_NULL,
                             null=True, blank=True, verbose_name='Работа')
    number = models.PositiveIntegerField('Номер варианта')
    tasks = models.ManyToManyField('tasks.Task', through='VariantTask',
                                   verbose_name='Задания')

    # Снимки данных работы на момент генерации
    work_name_snapshot = models.CharField('Название работы (снимок)',
                                          max_length=200, blank=True, default='')
    max_score_snapshot = models.PositiveIntegerField('Макс. балл (снимок)', default=100)
    duration_snapshot = models.PositiveIntegerField('Время (снимок)', default=45)

    # Тип варианта и персонализация
    VARIANT_TYPE_CHOICES = [
        ('regular', 'Обычный'),
        ('remedial', 'Работа над ошибками'),
        ('individual', 'Индивидуальный'),
    ]
    variant_type = models.CharField('Тип варианта', max_length=20,
                                    choices=VARIANT_TYPE_CHOICES, default='regular')
    assigned_student = models.ForeignKey(
        'students.Student', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_variants',
        verbose_name='Назначен ученику'
    )
    source_work = models.ForeignKey(
        'Work', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='remedial_variants',
        verbose_name='Работа-источник ошибок'
    )
    source_participation = models.ForeignKey(
        'events.EventParticipation',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='derived_remedial_variants',
        verbose_name='Исходная попытка ученика',
    )

    class Meta:
        verbose_name = 'Вариант'
        verbose_name_plural = 'Варианты'
        ordering = ['number']

    def __str__(self):
        name = self.work.name if self.work else self.work_name_snapshot
        return f"[{self.get_short_uuid()}] {name} - Вариант {self.number}"

    def get_absolute_url(self):
        return reverse('works:variant-detail', kwargs={'pk': self.pk})

class VariantTask(BaseModel):
    """Задание в варианте — иммутабельная запись с баллами"""
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, verbose_name='Вариант')
    task = models.ForeignKey(
        'tasks.Task',
        on_delete=models.PROTECT,
        verbose_name='Исходное задание',
        help_text='Связь с источником; печать использует сохранённый снимок.',
    )
    task_snapshot = models.JSONField(
        'Содержимое задания (снимок)',
        default=dict,
        help_text='Неизменяемое содержимое задания на момент генерации варианта.',
    )
    source_selection_id = models.CharField(
        'Исходный блок выбора заданий (снимок)',
        max_length=36,
        blank=True,
        default='',
        help_text=(
            'Идентификатор блока спецификации на момент генерации; '
            'не является внешним ключом.'
        ),
    )
    content_order = models.PositiveIntegerField(
        'Порядок исходного блока (снимок)',
        default=0,
    )
    order = models.PositiveIntegerField('Номер задания', default=0)
    max_points = models.PositiveIntegerField('Макс. баллов', default=0,
                                              help_text='Рассчитано при генерации из спецификации')
    # DEPRECATED: оставлено для обратной совместимости с генераторами
    weight = models.PositiveIntegerField('Вес (deprecated)', default=1)
    bank_role = models.CharField(
        'Роль задания',
        max_length=20,
        choices=TASK_BANK_ROLE_SPECIFIC_CHOICES,
        default=TASK_BANK_ROLE_CONTROL,
    )
    render_mode = models.CharField(
        'Режим печати',
        max_length=40,
        choices=TASK_RENDER_MODE_CHOICES,
        default=TASK_RENDER_MODE_TASK_ONLY,
    )
    is_assessable = models.BooleanField('Оценивать', default=True)
    blank_cells_after = models.BooleanField(
        'Пустые клетки после задания',
        default=False,
    )
    blank_cells_rows = models.PositiveIntegerField(
        'Строк клеток',
        default=DEFAULT_BLANK_CELLS_ROWS,
    )

    class Meta:
        verbose_name = 'Задание в варианте'
        verbose_name_plural = 'Задания в варианте'
        ordering = ['order']
        unique_together = ['variant', 'task']

    def __str__(self):
        return f"Вариант {self.variant.number} — #{self.order} ({self.max_points} балл.)"


class VariantContentBlockSnapshot(BaseModel):
    """Иммутабельный снимок незаданийного содержимого варианта."""

    variant = models.ForeignKey(
        Variant,
        on_delete=models.CASCADE,
        related_name='content_block_snapshots',
        verbose_name='Вариант',
    )
    source_content_id = models.CharField(
        'Исходный содержательный блок',
        max_length=36,
        blank=True,
        default='',
    )
    content_type = models.CharField(
        'Тип содержимого',
        max_length=20,
        choices=WorkContentBlock.CONTENT_TYPE_CHOICES,
    )
    order = models.PositiveIntegerField('Порядок в варианте', default=0)
    title = models.CharField('Заголовок (снимок)', max_length=200, blank=True)
    content = models.JSONField('Содержимое (снимок)', default=dict, blank=True)

    class Meta:
        verbose_name = 'Снимок содержательного блока варианта'
        verbose_name_plural = 'Снимки содержательных блоков вариантов'
        ordering = ['order', 'pk']

    def __str__(self):
        title = self.title or self.get_content_type_display()
        return f'{self.variant} — #{self.order} {title}'
