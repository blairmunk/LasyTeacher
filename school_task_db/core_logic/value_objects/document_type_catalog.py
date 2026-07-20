"""Catalog of supported document template types."""

from dataclasses import dataclass
from typing import Tuple

from core_logic.entities.document import (
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
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


@dataclass(frozen=True)
class DocumentTypeCatalogItem:
    document_type: str
    title: str
    description: str = ''
    source_type: str = ''
    is_renderable: bool = False
    renderer_types: Tuple[str, ...] = ()


SECTIONED_RENDERER_TYPES = ('html', 'pdf', 'latex')


DOCUMENT_TYPE_CATALOG = (
    DocumentTypeCatalogItem(
        document_type=WORK_DOCUMENT_TYPE,
        title='Контрольная / самостоятельная',
        description='Печатный документ по работе с вариантами.',
        source_type=WORK_SOURCE_TYPE,
        is_renderable=True,
        renderer_types=SECTIONED_RENDERER_TYPES,
    ),
    DocumentTypeCatalogItem(
        document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
        title='Работа над ошибками',
        description='Индивидуальный разбор и тренировка по remedial-варианту.',
        source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
        is_renderable=True,
        renderer_types=SECTIONED_RENDERER_TYPES,
    ),
    DocumentTypeCatalogItem(
        document_type=WORKSHEET_DOCUMENT_TYPE,
        title='Рабочий лист',
        description='Наборный документ с теорией и заданиями.',
    ),
    DocumentTypeCatalogItem(
        document_type=ANSWER_KEY_DOCUMENT_TYPE,
        title='Ключ для проверки',
        description='Отдельный документ с ответами и критериями.',
    ),
    DocumentTypeCatalogItem(
        document_type=HOMEWORK_DOCUMENT_TYPE,
        title='Домашнее задание',
        description='Документ для самостоятельной домашней работы.',
    ),
    DocumentTypeCatalogItem(
        document_type=DIAGNOSTIC_DOCUMENT_TYPE,
        title='Диагностическая карта',
        description='Диагностический документ по освоению тем.',
    ),
    DocumentTypeCatalogItem(
        document_type=CUSTOM_DOCUMENT_TYPE,
        title='Пользовательский',
        description='Свободный пользовательский шаблон.',
    ),
)


def get_document_type_catalog(
    renderable_only: bool = False,
) -> Tuple[DocumentTypeCatalogItem, ...]:
    return tuple(
        item
        for item in DOCUMENT_TYPE_CATALOG
        if not renderable_only or item.is_renderable
    )


def get_document_type_catalog_item(
    document_type: str,
) -> DocumentTypeCatalogItem | None:
    for item in get_document_type_catalog():
        if item.document_type == document_type:
            return item
    return None


def validate_document_type(document_type: str) -> None:
    if get_document_type_catalog_item(document_type) is None:
        raise ValueError(f'Unsupported document type: {document_type}')
