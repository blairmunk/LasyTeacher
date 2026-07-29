from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from core.models import BaseModel
from core_logic.entities.document import (
    DocumentPresentation,
    DocumentPresentationProfile,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_DOCUMENT_TYPE,
    CUSTOM_DOCUMENT_TYPE,
    DIAGNOSTIC_DOCUMENT_TYPE,
    HOMEWORK_DOCUMENT_TYPE,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)
from core_logic.value_objects.document_type_catalog import validate_document_type


class PrintSettings(BaseModel):
    """Persistence model for presentation profiles.

    The legacy class name is kept to avoid a database-table rename.
    """

    class DocumentType(models.TextChoices):
        WORK = WORK_DOCUMENT_TYPE, 'Контрольная / самостоятельная'
        REMEDIAL = REMEDIAL_SHEET_DOCUMENT_TYPE, 'Работа над ошибками'
        WORKSHEET = WORKSHEET_DOCUMENT_TYPE, 'Рабочий лист'
        ANSWER_KEY = ANSWER_KEY_DOCUMENT_TYPE, 'Ключ для проверки'
        HOMEWORK = HOMEWORK_DOCUMENT_TYPE, 'Домашнее задание'
        DIAGNOSTIC = DIAGNOSTIC_DOCUMENT_TYPE, 'Диагностическая карта'
        CUSTOM = CUSTOM_DOCUMENT_TYPE, 'Пользовательский'

    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    document_type = models.CharField(
        'Тип документа',
        max_length=50,
        choices=DocumentType.choices,
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

    is_default = models.BooleanField('Профиль печати по умолчанию', default=False)
    is_public = models.BooleanField('Доступен всем учителям', default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Создатель',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='print_settings_profiles',
    )

    class Meta:
        verbose_name = 'Профиль оформления'
        verbose_name_plural = 'Профили оформления'
        ordering = ['-is_default', 'document_type', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_document_type_display()})'

    def clean(self):
        super().clean()
        try:
            validate_document_type(self.document_type)
        except ValueError as error:
            raise ValidationError({'document_type': str(error)}) from error

    def to_presentation_profile(self):
        return DocumentPresentationProfile(
            name=self.name,
            document_type=self.document_type,
            presentation_profile_id=str(self.pk),
            description=self.description,
            is_default=self.is_default,
            presentation=DocumentPresentation(
                html_template_override=self.html_template_override,
                latex_template_override=self.latex_template_override,
                custom_css=self.custom_css,
                custom_latex_preamble=self.custom_latex_preamble,
            ),
        )
