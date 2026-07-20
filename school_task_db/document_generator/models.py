from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_DOCUMENT_TYPE,
    CUSTOM_DOCUMENT_TYPE,
    DIAGNOSTIC_DOCUMENT_TYPE,
    HOMEWORK_DOCUMENT_TYPE,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
    build_document_template_spec_from_config,
)
from core_logic.value_objects.document_section_catalog import (
    validate_document_section_types,
)


class DocumentTemplate(BaseModel):
    class TemplateType(models.TextChoices):
        WORK = WORK_DOCUMENT_TYPE, 'Контрольная / самостоятельная'
        REMEDIAL = REMEDIAL_SHEET_DOCUMENT_TYPE, 'Работа над ошибками'
        WORKSHEET = WORKSHEET_DOCUMENT_TYPE, 'Рабочий лист'
        ANSWER_KEY = ANSWER_KEY_DOCUMENT_TYPE, 'Ключ для проверки'
        HOMEWORK = HOMEWORK_DOCUMENT_TYPE, 'Домашнее задание'
        DIAGNOSTIC = DIAGNOSTIC_DOCUMENT_TYPE, 'Диагностическая карта'
        CUSTOM = CUSTOM_DOCUMENT_TYPE, 'Пользовательский'

    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    template_type = models.CharField(
        'Тип шаблона',
        max_length=50,
        choices=TemplateType.choices,
    )

    sections_config = models.JSONField(
        'Конфигурация секций',
        default=list,
        blank=True,
        help_text='JSON: [{"type": "header", "params": {...}}, ...]',
    )
    default_content_config = models.JSONField(
        'Параметры контента по умолчанию',
        default=dict,
        blank=True,
    )

    latex_template_override = models.TextField(
        'Переопределение LaTeX-шаблона',
        blank=True,
    )
    html_template_override = models.TextField(
        'Переопределение HTML-шаблона',
        blank=True,
    )
    custom_css = models.TextField('Пользовательский CSS', blank=True)
    custom_latex_preamble = models.TextField(
        'Пользовательская LaTeX-преамбула',
        blank=True,
    )

    is_default = models.BooleanField('Шаблон по умолчанию', default=False)
    is_public = models.BooleanField('Доступен всем учителям', default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Создатель',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='document_templates',
    )

    class Meta:
        verbose_name = 'Шаблон документа'
        verbose_name_plural = 'Шаблоны документов'
        ordering = ['-is_default', 'template_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_template_type_display()})'

    def clean(self):
        super().clean()
        try:
            template_spec = self.to_template_spec()
            validate_document_section_types(
                self.template_type,
                template_spec.section_types,
            )
        except ValueError as error:
            raise ValidationError({'sections_config': str(error)}) from error

    def to_template_spec(self):
        return build_document_template_spec_from_config(
            name=self.name,
            template_type=self.template_type,
            sections_config=self.sections_config,
            default_content_config=self.default_content_config,
        )
