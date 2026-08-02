"""Factories for document render plans."""

from collections.abc import Callable

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
    DocumentPresentationProfile,
    EVENT_REPORT_SOURCE_TYPE,
    REMEDIAL_WORK_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    STUDENT_DIGEST_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
)
from core_logic.value_objects.document_render_plan import (
    DocumentRenderPlan,
    build_document_render_plan,
)
from core_logic.value_objects.document_recipe_factories import (
    build_event_performance_report_document_recipe,
    build_remedial_sheet_document_recipe,
    build_student_digest_document_recipe,
    build_work_document_recipe,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    COMMON_HEADER_SECTION,
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    HEADER_SECTION,
    PAGE_BREAK_SECTION,
    STUDENT_DIGEST_DOCUMENT_TYPE,
    TASK_LIST_SECTION,
)


def build_work_document_render_plan(
    work_id: str,
    work_name: str,
    options: WorkDocumentRenderOptions,
    presentation_profile: DocumentPresentationProfile | None = None,
    variant_ids: list[str] | None = None,
) -> DocumentRenderPlan:
    return build_document_render_plan(
        source=build_work_document_source(
            work_id=work_id,
            work_name=work_name,
        ),
        recipe=build_work_document_recipe_for_render(
            options=options,
            presentation_profile=presentation_profile,
            variant_ids=variant_ids,
        ),
        render_target=options.render_target,
    )


def build_remedial_sheet_document_render_plan(
    variant_id: str,
    options: RemedialSheetDocumentRenderOptions,
    presentation_profile: DocumentPresentationProfile | None = None,
) -> DocumentRenderPlan:
    return build_document_render_plan(
        source=build_remedial_sheet_document_source(variant_id),
        recipe=build_remedial_sheet_document_recipe_for_render(
            options=options,
            presentation_profile=presentation_profile,
        ),
        render_target=options.render_target,
    )


def build_remedial_sheet_batch_document_render_plan(
    work_id: str,
    work_name: str,
    variant_ids: list[str],
    options: RemedialSheetDocumentRenderOptions,
    presentation_profile: DocumentPresentationProfile | None = None,
) -> DocumentRenderPlan:
    return build_document_render_plan(
        source=build_remedial_sheet_batch_document_source(
            work_id=work_id,
            work_name=work_name,
        ),
        recipe=build_remedial_sheet_batch_document_recipe_for_render(
            variant_ids=variant_ids,
            options=options,
            presentation_profile=presentation_profile,
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


def build_event_report_document_source(
    event_id: str,
    event_name: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=EVENT_REPORT_SOURCE_TYPE,
        source_id=event_id,
        title=event_name,
    )


def build_student_digest_document_source(
    group_id: str,
    group_name: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=STUDENT_DIGEST_SOURCE_TYPE,
        source_id=group_id,
        title=f'Дайджест оценок: {group_name}',
    )


def build_work_document_recipe_for_render(
    options: WorkDocumentRenderOptions,
    presentation_profile: DocumentPresentationProfile | None = None,
    variant_ids: list[str] | None = None,
) -> DocumentRecipe:
    recipe = _recipe_with_profile_presentation(
        presentation_profile=presentation_profile,
        default_recipe_builder=build_work_document_recipe,
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


def build_remedial_sheet_document_recipe_for_render(
    options: RemedialSheetDocumentRenderOptions,
    presentation_profile: DocumentPresentationProfile | None = None,
) -> DocumentRecipe:
    return _recipe_with_profile_presentation(
        presentation_profile=presentation_profile,
        default_recipe_builder=(
            lambda: build_remedial_sheet_document_recipe(
                options.build_options,
            )
        ),
    )


def build_remedial_sheet_batch_document_recipe_for_render(
    variant_ids: list[str],
    options: RemedialSheetDocumentRenderOptions,
    presentation_profile: DocumentPresentationProfile | None = None,
) -> DocumentRecipe:
    base_recipe = build_remedial_sheet_document_recipe_for_render(
        options=options,
        presentation_profile=presentation_profile,
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
        presentation=base_recipe.presentation,
    )


def build_event_report_document_recipe_for_render(
    presentation_profile: DocumentPresentationProfile | None = None,
    include_content_element_text: bool = True,
    include_teacher_notes: bool = False,
) -> DocumentRecipe:
    return _recipe_with_profile_presentation(
        presentation_profile=presentation_profile,
        default_recipe_builder=lambda: (
            build_event_performance_report_document_recipe(
                include_content_element_text=include_content_element_text,
                include_teacher_notes=include_teacher_notes,
            )
        ),
    )


def build_student_digest_document_recipe_for_render(
    digest_request,
    student_ids: list[str],
    presentation_profile: DocumentPresentationProfile | None = None,
) -> DocumentRecipe:
    base_recipe = _recipe_with_profile_presentation(
        presentation_profile=presentation_profile,
        default_recipe_builder=(
            lambda: build_student_digest_document_recipe(
                digest_request.options,
            )
        ),
    )
    sections = []
    for index, student_id in enumerate(student_ids):
        if index > 0:
            sections.append(DocumentSectionSpec(section_type=PAGE_BREAK_SECTION))
        sections.extend(
            DocumentSectionSpec(
                section_type=section.section_type,
                title=section.title,
                options={
                    **dict(section.options),
                    'digest_request': digest_request,
                    'student_id': student_id,
                },
            )
            for section in base_recipe.sections
        )
    return DocumentRecipe(
        document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
        sections=sections,
        presentation=base_recipe.presentation,
    )


def _recipe_with_profile_presentation(
    presentation_profile: DocumentPresentationProfile | None,
    default_recipe_builder: Callable[[], DocumentRecipe],
) -> DocumentRecipe:
    recipe = default_recipe_builder()
    if presentation_profile is None:
        return recipe
    return DocumentRecipe(
        document_type=recipe.document_type,
        sections=recipe.sections,
        presentation=presentation_profile.presentation,
    )


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
