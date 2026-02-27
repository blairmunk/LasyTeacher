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

    def get_content_tree(self):
        """Дерево содержания: только корневые элементы (children подтянутся)"""
        return self.content_entries.filter(
            parent__isnull=True
        ).order_by('code')

    def get_coverage(self, tasks_qs=None):
        """
        Покрытие заданиями.
        tasks_qs — опционально фильтр заданий (например, задания одной работы)
        """
        leaves = self.content_entries.filter(children__isnull=True)
        total = leaves.count()
        if not total:
            return {'total': 0, 'covered': 0, 'pct': 0}

        if tasks_qs is not None:
            covered = leaves.filter(topic__task__in=tasks_qs).distinct().count()
        else:
            covered = leaves.filter(topic__task__isnull=False).distinct().count()

        return {
            'total': total,
            'covered': covered,
            'uncovered': total - covered,
            'pct': round(covered / total * 100) if total else 0,
        }


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

    @property
    def level(self):
        """Уровень вложенности по коду: '1'→0, '1.4'→1, '1.1.6'→2"""
        return self.code.count('.')

    @property
    def is_leaf(self):
        """Конечный элемент (нет дочерних)"""
        return not self.children.exists()

    def get_task_count(self):
        """Количество заданий через subtopic или topic"""
        if self.subtopic:
            return self.subtopic.task_set.count()
        if self.topic:
            return self.topic.task_set.count()
        return 0

    def get_tasks(self):
        """Задания этого элемента (точная привязка)"""
        from tasks.models import Task
        if self.subtopic:
            return Task.objects.filter(subtopic=self.subtopic)
        if self.topic:
            return Task.objects.filter(topic=self.topic)
        return Task.objects.none()

    def get_all_tasks(self):
        """Задания включая дочерние элементы"""
        from tasks.models import Task
        q = models.Q()

        # Собираем все topic_id и subtopic_id из дерева
        entries = [self]
        for child in self.children.select_related('topic', 'subtopic'):
            entries.append(child)
            for grandchild in child.children.select_related('topic', 'subtopic'):
                entries.append(grandchild)

        for entry in entries:
            if entry.subtopic_id:
                q |= models.Q(subtopic_id=entry.subtopic_id)
            elif entry.topic_id:
                q |= models.Q(topic_id=entry.topic_id)

        if not q:
            return Task.objects.none()
        return Task.objects.filter(q).distinct()

    def get_sibling_codes(self):
        """Эта же тема в других кодификаторах"""
        q = models.Q()
        if self.subtopic:
            q = models.Q(subtopic=self.subtopic)
        elif self.topic:
            q = models.Q(topic=self.topic)
        else:
            return ContentEntry.objects.none()
        return ContentEntry.objects.filter(q).exclude(
            pk=self.pk
        ).select_related('codifier')


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

    def get_task_count(self):
        return self.tasks.count()
