"""Factories for document recipes prepared for rendering."""

from collections.abc import Callable

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentPresentationProfile,
)
from core_logic.value_objects.document_render_options import (
    RemedialSheetDocumentRenderOptions,
    WorkDocumentRenderOptions,
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
    if has_variant_header:
        repeated_sections = [
            _section_with_options(
                section,
                {
                    **dict(section.options),
                    'show_variant_heading': False,
                },
            )
            if section.section_type == TASK_LIST_SECTION
            else section
            for section in repeated_sections
        ]
    sections = [
        *common_sections,
        *repeat_document_sections(
            repeated_sections,
            ({'variant_id': variant_id} for variant_id in variant_ids),
            break_between_instances=break_between_variants,
        ),
    ]
    return DocumentRecipe(
        document_type=recipe.document_type,
        sections=sections,
        presentation=recipe.presentation,
    )


def repeat_document_sections(
    sections,
    instance_options,
    break_between_instances: bool = True,
) -> tuple[DocumentSectionSpec, ...]:
    """Repeat one section sequence for each distributable document item."""
    instances = tuple(instance_options)
    repeated_sections = []
    for index, options in enumerate(instances):
        if break_between_instances and index > 0:
            repeated_sections.append(
                DocumentSectionSpec(section_type=PAGE_BREAK_SECTION),
            )
        for section in sections:
            section_options = {
                **dict(section.options),
                **dict(options),
            }
            repeated_sections.append(
                _section_with_options(
                    section,
                    section_options,
                )
            )
    return tuple(repeated_sections)


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
    return DocumentRecipe(
        document_type=base_recipe.document_type,
        sections=repeat_document_sections(
            base_recipe.sections,
            ({'variant_id': variant_id} for variant_id in variant_ids),
        ),
        presentation=base_recipe.presentation,
    )


def build_event_report_document_recipe_for_render(
    presentation_profile: DocumentPresentationProfile | None = None,
    options=None,
) -> DocumentRecipe:
    return _recipe_with_profile_presentation(
        presentation_profile=presentation_profile,
        default_recipe_builder=lambda: (
            build_event_performance_report_document_recipe(
                options=options,
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
    return DocumentRecipe(
        document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
        sections=repeat_document_sections(
            base_recipe.sections,
            (
                {
                    'digest_request': digest_request,
                    'student_id': student_id,
                }
                for student_id in student_ids
            ),
        ),
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
