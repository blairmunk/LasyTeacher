"""Factories for document render plans."""

from collections.abc import Callable

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    PrintSettingsSpec,
    REMEDIAL_WORK_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
    WORK_DOCUMENT_STYLE_WORKSHEET,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderPlan,
    build_document_render_plan,
)
from core_logic.value_objects.document_recipe_factories import (
    build_remedial_sheet_document_recipe,
    build_worksheet_work_document_recipe,
    build_work_document_recipe,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    COMMON_HEADER_SECTION,
    HEADER_SECTION,
    PAGE_BREAK_SECTION,
    TASK_LIST_SECTION,
    THEORY_SECTION,
)


def build_work_document_render_plan(
    work_id: str,
    work_name: str,
    options: WorkDocumentRenderOptions,
    print_settings_spec: PrintSettingsSpec | None = None,
    variant_ids: list[str] | None = None,
) -> DocumentRenderPlan:
    return build_document_render_plan(
        source=build_work_document_source(
            work_id=work_id,
            work_name=work_name,
        ),
        recipe=build_work_document_recipe_for_render(
            options=options,
            print_settings_spec=print_settings_spec,
            variant_ids=variant_ids,
        ),
        render_target=options.render_target,
    )


def build_remedial_sheet_document_render_plan(
    variant_id: str,
    options: RemedialSheetDocumentRenderOptions,
    print_settings_spec: PrintSettingsSpec | None = None,
) -> DocumentRenderPlan:
    return build_document_render_plan(
        source=build_remedial_sheet_document_source(variant_id),
        recipe=build_remedial_sheet_document_recipe_for_render(
            options=options,
            print_settings_spec=print_settings_spec,
        ),
        render_target=options.render_target,
    )


def build_remedial_sheet_batch_document_render_plan(
    work_id: str,
    work_name: str,
    variant_ids: list[str],
    options: RemedialSheetDocumentRenderOptions,
    print_settings_spec: PrintSettingsSpec | None = None,
) -> DocumentRenderPlan:
    return build_document_render_plan(
        source=build_remedial_sheet_batch_document_source(
            work_id=work_id,
            work_name=work_name,
        ),
        recipe=build_remedial_sheet_batch_document_recipe_for_render(
            variant_ids=variant_ids,
            options=options,
            print_settings_spec=print_settings_spec,
        ),
        render_target=options.render_target,
    )


def build_work_document_source(
    work_id: str,
    work_name: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=WORK_SOURCE_TYPE,
        source_id=work_id,
        title=work_name,
    )


def build_remedial_sheet_document_source(
    variant_id: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
        source_id=variant_id,
        title='Работа над ошибками',
    )


def build_remedial_sheet_batch_document_source(
    work_id: str,
    work_name: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=REMEDIAL_WORK_SOURCE_TYPE,
        source_id=work_id,
        title=work_name,
    )


def build_work_document_recipe_for_render(
    options: WorkDocumentRenderOptions,
    print_settings_spec: PrintSettingsSpec | None = None,
    variant_ids: list[str] | None = None,
) -> DocumentRecipe:
    recipe = _recipe_from_print_settings_or_default(
        print_settings_spec=print_settings_spec,
        default_recipe_builder=(
            lambda: _build_default_work_recipe(options)
        ),
    )
    recipe = apply_work_document_print_overrides(recipe, options)
    return expand_work_document_recipe_per_variant(
        recipe,
        variant_ids,
        break_between_variants=options.break_between_variants,
    )


def expand_work_document_recipe_per_variant(
    recipe: DocumentRecipe,
    variant_ids: list[str] | None,
    break_between_variants: bool = True,
) -> DocumentRecipe:
    if not variant_ids:
        return recipe

    common_sections = [
        section
        for section in recipe.sections
        if section.section_type == COMMON_HEADER_SECTION
    ]
    repeated_sections = [
        section
        for section in recipe.sections
        if section.section_type != COMMON_HEADER_SECTION
    ]
    has_variant_header = any(
        section.section_type == HEADER_SECTION
        for section in repeated_sections
    )
    sections = list(common_sections)
    last_index = len(variant_ids) - 1
    for index, variant_id in enumerate(variant_ids):
        for section in repeated_sections:
            section_options = {
                **dict(section.options),
                'variant_id': variant_id,
            }
            if (
                section.section_type == TASK_LIST_SECTION
                and has_variant_header
            ):
                section_options['show_variant_heading'] = False
            sections.append(
                _section_with_options(
                    section,
                    section_options,
                )
            )
        if break_between_variants and index < last_index:
            sections.append(DocumentSectionSpec(section_type=PAGE_BREAK_SECTION))
    return DocumentRecipe(
        document_type=recipe.document_type,
        sections=sections,
        presentation=recipe.presentation,
    )


def apply_work_document_print_overrides(
    recipe: DocumentRecipe,
    options: WorkDocumentRenderOptions,
) -> DocumentRecipe:
    overrides = options.print_overrides
    sections = []
    for section in recipe.sections:
        if (
            overrides.hide_theory
            and section.section_type == THEORY_SECTION
        ):
            continue
        if (
            overrides.hide_blank_cells
            and section.section_type == BLANK_CELLS_SECTION
        ):
            continue
        if section.section_type != TASK_LIST_SECTION:
            sections.append(section)
            continue

        section_options = dict(section.options)
        hidden_content_types = _content_types_option(
            section_options.get('hidden_content_types'),
        )
        for content_type in overrides.hidden_content_types:
            if content_type not in hidden_content_types:
                hidden_content_types.append(content_type)
        if hidden_content_types:
            section_options['hidden_content_types'] = hidden_content_types
        if overrides.hide_blank_cells:
            section_options['hide_blank_cells'] = True
        sections.append(_section_with_options(section, section_options))

    if overrides.append_answers:
        sections = [
            section
            for section in sections
            if section.section_type not in (
                ANSWERS_SECTION,
                ANSWER_KEY_SECTION,
            )
        ]
        sections.append(DocumentSectionSpec(section_type=ANSWERS_SECTION))

    return DocumentRecipe(
        document_type=recipe.document_type,
        sections=sections,
        presentation=recipe.presentation,
    )


def _build_default_work_recipe(
    options: WorkDocumentRenderOptions,
) -> DocumentRecipe:
    if options.document_style == WORK_DOCUMENT_STYLE_WORKSHEET:
        return build_worksheet_work_document_recipe(options.build_options)
    return build_work_document_recipe(options.build_options)


def build_remedial_sheet_document_recipe_for_render(
    options: RemedialSheetDocumentRenderOptions,
    print_settings_spec: PrintSettingsSpec | None = None,
) -> DocumentRecipe:
    return _recipe_from_print_settings_or_default(
        print_settings_spec=print_settings_spec,
        default_recipe_builder=(
            lambda: build_remedial_sheet_document_recipe(
                options.build_options,
            )
        ),
    )


def build_remedial_sheet_batch_document_recipe_for_render(
    variant_ids: list[str],
    options: RemedialSheetDocumentRenderOptions,
    print_settings_spec: PrintSettingsSpec | None = None,
) -> DocumentRecipe:
    base_recipe = build_remedial_sheet_document_recipe_for_render(
        options=options,
        print_settings_spec=print_settings_spec,
    )
    sections = []
    for index, variant_id in enumerate(variant_ids):
        if index > 0:
            sections.append(DocumentSectionSpec(section_type=PAGE_BREAK_SECTION))
        sections.extend(
            DocumentSectionSpec(
                section_type=section.section_type,
                title=section.title,
                options={
                    **dict(section.options),
                    'variant_id': variant_id,
                },
            )
            for section in base_recipe.sections
        )
    return DocumentRecipe(
        document_type=base_recipe.document_type,
        sections=sections,
    )


def _recipe_from_print_settings_or_default(
    print_settings_spec: PrintSettingsSpec | None,
    default_recipe_builder: Callable[[], DocumentRecipe],
) -> DocumentRecipe:
    if print_settings_spec:
        return print_settings_spec.to_print_recipe()
    return default_recipe_builder()


def _section_with_options(
    section: DocumentSectionSpec,
    options: dict,
) -> DocumentSectionSpec:
    return DocumentSectionSpec(
        section_type=section.section_type,
        title=section.title,
        options=options,
    )


def _content_types_option(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [
            item.strip()
            for item in value.split(',')
            if item.strip()
        ]
    return list(value)
