"""Catalog of supported section types for document print profiles."""

from dataclasses import dataclass, field
from typing import Any, Mapping, Tuple

from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_DOCUMENT_TYPE,
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    COMMON_HEADER_SECTION,
    CUSTOM_DOCUMENT_TYPE,
    DIAGNOSTIC_DOCUMENT_TYPE,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    HOMEWORK_DOCUMENT_TYPE,
    ORIGINAL_MISTAKES_SECTION,
    PAGE_BREAK_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SCORE_TABLE_SECTION,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
)
from core_logic.value_objects.task_print_settings import (
    DEFAULT_BLANK_CELLS_COLUMNS,
    DEFAULT_BLANK_CELLS_ROW_HEIGHT,
    DEFAULT_BLANK_CELLS_ROWS,
)
from core_logic.value_objects.variant_content_snapshot import (
    VARIANT_STATIC_CONTENT_TYPES,
)


@dataclass(frozen=True)
class DocumentSectionCatalogItem:
    section_type: str
    title: str
    supported_document_types: Tuple[str, ...]
    renderable_document_types: Tuple[str, ...] = ()
    description: str = ''
    is_repeatable: bool = False
    is_fixed_order: bool = False
    options_hint: str = ''
    options_example: Mapping[str, Any] = field(default_factory=dict)

    def supports_document_type(self, document_type: str) -> bool:
        return (
            not document_type
            or document_type in self.supported_document_types
        )

    def is_renderable_for(self, document_type: str) -> bool:
        return (
            not document_type
            and bool(self.renderable_document_types)
        ) or document_type in self.renderable_document_types

    @property
    def has_options(self) -> bool:
        return bool(self.options_hint or self.options_example)


ALL_DOCUMENT_TYPES = (
    WORK_DOCUMENT_TYPE,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
    ANSWER_KEY_DOCUMENT_TYPE,
    HOMEWORK_DOCUMENT_TYPE,
    DIAGNOSTIC_DOCUMENT_TYPE,
    CUSTOM_DOCUMENT_TYPE,
)

TASK_DOCUMENT_TYPES = (
    WORK_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
    HOMEWORK_DOCUMENT_TYPE,
    DIAGNOSTIC_DOCUMENT_TYPE,
    CUSTOM_DOCUMENT_TYPE,
)

SOLUTION_DOCUMENT_TYPES = (
    WORK_DOCUMENT_TYPE,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    WORKSHEET_DOCUMENT_TYPE,
    ANSWER_KEY_DOCUMENT_TYPE,
    HOMEWORK_DOCUMENT_TYPE,
    DIAGNOSTIC_DOCUMENT_TYPE,
    CUSTOM_DOCUMENT_TYPE,
)

DOCUMENT_SECTION_CATALOG = (
    DocumentSectionCatalogItem(
        section_type=COMMON_HEADER_SECTION,
        title='Общий заголовок',
        supported_document_types=(WORK_DOCUMENT_TYPE,),
        renderable_document_types=(WORK_DOCUMENT_TYPE,),
        description='Заголовок для всей распечатки перед вариантами.',
        is_fixed_order=True,
    ),
    DocumentSectionCatalogItem(
        section_type=HEADER_SECTION,
        title='Заголовок',
        supported_document_types=ALL_DOCUMENT_TYPES,
        renderable_document_types=(
            WORK_DOCUMENT_TYPE,
            REMEDIAL_SHEET_DOCUMENT_TYPE,
        ),
        description='Название документа и основные метаданные.',
        is_repeatable=True,
    ),
    DocumentSectionCatalogItem(
        section_type=TASK_LIST_SECTION,
        title='Список заданий',
        supported_document_types=TASK_DOCUMENT_TYPES,
        renderable_document_types=(WORK_DOCUMENT_TYPE,),
        description=(
            'Контент варианта в порядке, заданном спецификацией работы.'
        ),
        is_repeatable=True,
        options_hint=(
            'Можно скрыть теоретические или текстовые блоки. '
            'Роли, решения и клетки определяются спецификацией работы.'
        ),
        options_example={
            'hidden_content_types': ['theory'],
        },
    ),
    DocumentSectionCatalogItem(
        section_type=ANSWERS_SECTION,
        title='Ответы',
        supported_document_types=SOLUTION_DOCUMENT_TYPES,
        renderable_document_types=(
            WORK_DOCUMENT_TYPE,
            REMEDIAL_SHEET_DOCUMENT_TYPE,
        ),
        description='Блок кратких ответов.',
    ),
    DocumentSectionCatalogItem(
        section_type=ANSWER_KEY_SECTION,
        title='Ключ ответов',
        supported_document_types=(
            WORK_DOCUMENT_TYPE,
            ANSWER_KEY_DOCUMENT_TYPE,
            CUSTOM_DOCUMENT_TYPE,
        ),
        renderable_document_types=(WORK_DOCUMENT_TYPE,),
        description='Отдельный ключ для проверки или старый блок ответов работы.',
    ),
    DocumentSectionCatalogItem(
        section_type=SHORT_SOLUTIONS_SECTION,
        title='Краткие решения',
        supported_document_types=SOLUTION_DOCUMENT_TYPES,
        renderable_document_types=(
            WORK_DOCUMENT_TYPE,
            REMEDIAL_SHEET_DOCUMENT_TYPE,
        ),
        description='Блок кратких разборов.',
    ),
    DocumentSectionCatalogItem(
        section_type=FULL_SOLUTIONS_SECTION,
        title='Полные решения',
        supported_document_types=SOLUTION_DOCUMENT_TYPES,
        renderable_document_types=(
            WORK_DOCUMENT_TYPE,
            REMEDIAL_SHEET_DOCUMENT_TYPE,
        ),
        description='Блок подробных решений.',
        is_repeatable=True,
    ),
    DocumentSectionCatalogItem(
        section_type=ORIGINAL_MISTAKES_SECTION,
        title='Ошибки исходной работы',
        supported_document_types=(REMEDIAL_SHEET_DOCUMENT_TYPE,),
        renderable_document_types=(REMEDIAL_SHEET_DOCUMENT_TYPE,),
        description='Разбор заданий, ошибочно решенных в исходной работе.',
    ),
    DocumentSectionCatalogItem(
        section_type=TRAINING_TASKS_SECTION,
        title='Тренировочные задания',
        supported_document_types=(REMEDIAL_SHEET_DOCUMENT_TYPE,),
        renderable_document_types=(REMEDIAL_SHEET_DOCUMENT_TYPE,),
        description='Новые задания для работы над ошибками.',
    ),
    DocumentSectionCatalogItem(
        section_type=PAGE_BREAK_SECTION,
        title='Разрыв страницы',
        supported_document_types=ALL_DOCUMENT_TYPES,
        renderable_document_types=(
            WORK_DOCUMENT_TYPE,
            REMEDIAL_SHEET_DOCUMENT_TYPE,
        ),
        description='Техническая секция для управления печатной версткой.',
        is_repeatable=True,
    ),
    DocumentSectionCatalogItem(
        section_type=BLANK_CELLS_SECTION,
        title='Пустые клетки',
        supported_document_types=ALL_DOCUMENT_TYPES,
        renderable_document_types=(
            WORK_DOCUMENT_TYPE,
            REMEDIAL_SHEET_DOCUMENT_TYPE,
        ),
        description='Разлинованное место для решения или черновика.',
        is_repeatable=True,
        options_hint='Размер отдельного блока клеток.',
        options_example={
            'rows': DEFAULT_BLANK_CELLS_ROWS,
            'columns': DEFAULT_BLANK_CELLS_COLUMNS,
            'row_height': DEFAULT_BLANK_CELLS_ROW_HEIGHT,
        },
    ),
    DocumentSectionCatalogItem(
        section_type=SCORE_TABLE_SECTION,
        title='Критерии оценивания',
        supported_document_types=(
            WORK_DOCUMENT_TYPE,
            WORKSHEET_DOCUMENT_TYPE,
            HOMEWORK_DOCUMENT_TYPE,
            DIAGNOSTIC_DOCUMENT_TYPE,
            CUSTOM_DOCUMENT_TYPE,
        ),
        renderable_document_types=(WORK_DOCUMENT_TYPE,),
        description='Таблица шкалы и критериев оценивания.',
    ),
)


def get_document_section_catalog(
    document_type: str = '',
    renderable_only: bool = False,
) -> Tuple[DocumentSectionCatalogItem, ...]:
    return tuple(
        item
        for item in DOCUMENT_SECTION_CATALOG
        if item.supports_document_type(document_type)
        and (not renderable_only or item.is_renderable_for(document_type))
    )


def get_document_section_catalog_item(
    section_type: str,
) -> DocumentSectionCatalogItem | None:
    for item in get_document_section_catalog():
        if item.section_type == section_type:
            return item
    return None


def order_document_section_types(
    selected_section_types,
    section_order,
) -> Tuple[str, ...]:
    selected = [
        section_type.strip()
        for section_type in selected_section_types
        if section_type.strip()
    ]
    selected_set = set(selected)
    fixed_order_sections = [
        section_type
        for section_type in selected
        if section_type == COMMON_HEADER_SECTION
    ]
    ordered = [
        section_type.strip()
        for section_type in _section_order_items(section_order)
        if (
            section_type.strip() in selected_set
            and section_type.strip() not in fixed_order_sections
        )
    ]
    seen = set(ordered)
    ordered.extend(
        section_type
        for section_type in selected
        if (
            section_type not in seen
            and section_type not in fixed_order_sections
        )
    )
    return tuple(fixed_order_sections + ordered)


def validate_document_section_types(
    document_type: str,
    section_types,
) -> None:
    for section_type in section_types:
        item = get_document_section_catalog_item(section_type)
        if item is None:
            raise ValueError(f'Unsupported document section: {section_type}')
        if not item.supports_document_type(document_type):
            raise ValueError(
                f'Section {section_type} is not supported '
                f'for document type {document_type}'
            )


def validate_document_section_specs(
    document_type: str,
    sections,
) -> None:
    sections = tuple(sections)
    validate_document_section_types(
        document_type,
        (section.section_type for section in sections),
    )
    for section in sections:
        _validate_document_section_options(
            section.section_type,
            section.options,
        )


def _validate_document_section_options(section_type, options) -> None:
    options = dict(options or {})
    if section_type == BLANK_CELLS_SECTION:
        _validate_blank_cells_options(options)
    elif section_type == TASK_LIST_SECTION:
        _validate_task_list_options(options)


def _validate_blank_cells_options(options) -> None:
    for option_name, max_value in (
        ('rows', 40),
        ('columns', 40),
        ('row_height', 120),
    ):
        if option_name not in options:
            continue
        value = options[option_name]
        try:
            parsed_value = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f'Section {BLANK_CELLS_SECTION} option '
                f'{option_name} must be an integer'
            ) from error
        if isinstance(value, bool) or not 1 <= parsed_value <= max_value:
            raise ValueError(
                f'Section {BLANK_CELLS_SECTION} option {option_name} '
                f'must be between 1 and {max_value}'
            )


def _validate_task_list_options(options) -> None:
    hidden_content_types = options.get('hidden_content_types')
    if hidden_content_types is not None:
        if isinstance(hidden_content_types, str):
            hidden_content_types = [
                item.strip()
                for item in hidden_content_types.split(',')
                if item.strip()
            ]
        elif isinstance(hidden_content_types, (list, tuple)):
            hidden_content_types = list(hidden_content_types)
        else:
            raise ValueError(
                f'Section {TASK_LIST_SECTION} option '
                'hidden_content_types must be a list or string'
            )
        if any(
            not isinstance(content_type, str)
            for content_type in hidden_content_types
        ):
            raise ValueError(
                f'Section {TASK_LIST_SECTION} option '
                'hidden_content_types must contain strings'
            )
        unsupported_content_types = sorted(
            set(hidden_content_types) - VARIANT_STATIC_CONTENT_TYPES
        )
        if unsupported_content_types:
            raise ValueError(
                f'Section {TASK_LIST_SECTION} option '
                'hidden_content_types contains unsupported values: '
                f'{", ".join(unsupported_content_types)}'
            )

    if (
        'hide_blank_cells' in options
        and not isinstance(options['hide_blank_cells'], bool)
    ):
        raise ValueError(
            f'Section {TASK_LIST_SECTION} option hide_blank_cells '
            'must be boolean'
        )


def _section_order_items(section_order):
    if isinstance(section_order, str):
        return section_order.split(',')
    return section_order or ()
