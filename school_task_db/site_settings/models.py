from django.db import models


class SiteSettings(models.Model):
    """Singleton — настройки сайта (всегда одна запись)"""

    # Школа
    school_name = models.CharField(
        'Название школы', max_length=200, blank=True,
        default='', help_text='Для шапки документов'
    )
    teacher_name = models.CharField(
        'ФИО учителя', max_length=200, blank=True,
        default='', help_text='Для шапки документов'
    )

    # Предмет по умолчанию
    default_subject = models.CharField(
        'Предмет по умолчанию', max_length=100, blank=True,
        default='Физика', help_text='Используется при импорте и создании'
    )

    # Баллы
    points_scale = models.IntegerField(
        'Шкала баллов', default=100,
        help_text='Макс. балл за работу по умолчанию'
    )

    # Учебный год
    current_academic_year = models.CharField(
        'Текущий учебный год', max_length=20, blank=True,
        default='2025-2026'
    )

    # Логотип для PDF
    logo = models.ImageField(
        'Логотип школы', upload_to='settings/',
        blank=True, null=True,
        help_text='Для шапки PDF-документов'
    )

    # Генерация
    default_variants_count = models.IntegerField(
        'Кол-во вариантов по умолчанию', default=2,
        help_text='При генерации работы'
    )

    # PDF настройки
    pdf_font_size = models.IntegerField(
        'Размер шрифта PDF', default=12,
        help_text='pt'
    )
    pdf_margin_top = models.IntegerField(
        'Отступ сверху PDF', default=15,
        help_text='мм'
    )
    pdf_margin_bottom = models.IntegerField(
        'Отступ снизу PDF', default=15,
        help_text='мм'
    )

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return 'Настройки сайта'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Запрет удаления singleton

    @classmethod
    def get(cls):
        """Получить единственный экземпляр (создать если нет)"""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
