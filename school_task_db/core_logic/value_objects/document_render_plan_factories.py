"""Factories for document render plans."""

from collections.abc import Callable

from core_logic.entities.document import (
    DocumentRecipe,
    DocumentSourceRef,
    DocumentTemplateSpec,
    REMEDIAL_VARIANT_SOURCE_TYPE,
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
    build_remedial_sheet_document_recipe,
    build_work_document_recipe,
)


def build_work_document_render_plan(
    work_id: str,
    work_name: str,
    options: WorkDocumentRenderOptions,
    template_spec: DocumentTemplateSpec | None = None,
) -> DocumentRenderPlan:
    return build_document_render_plan(
        source=build_work_document_source(
            work_id=work_id,
            work_name=work_name,
        ),
        recipe=build_work_document_recipe_for_render(
            options=options,
            template_spec=template_spec,
        ),
        render_target=options.render_target,
    )


def build_remedial_sheet_document_render_plan(
    variant_id: str,
    options: RemedialSheetDocumentRenderOptions,
    template_spec: DocumentTemplateSpec | None = None,
) -> DocumentRenderPlan:
    return build_document_render_plan(
        source=build_remedial_sheet_document_source(variant_id),
        recipe=build_remedial_sheet_document_recipe_for_render(
            options=options,
            template_spec=template_spec,
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


def build_work_document_recipe_for_render(
    options: WorkDocumentRenderOptions,
    template_spec: DocumentTemplateSpec | None = None,
) -> DocumentRecipe:
    return _recipe_from_template_or_default(
        template_spec=template_spec,
        default_recipe_builder=(
            lambda: build_work_document_recipe(options.build_options)
        ),
    )


def build_remedial_sheet_document_recipe_for_render(
    options: RemedialSheetDocumentRenderOptions,
    template_spec: DocumentTemplateSpec | None = None,
) -> DocumentRecipe:
    return _recipe_from_template_or_default(
        template_spec=template_spec,
        default_recipe_builder=(
            lambda: build_remedial_sheet_document_recipe(
                options.build_options,
            )
        ),
    )


def _recipe_from_template_or_default(
    template_spec: DocumentTemplateSpec | None,
    default_recipe_builder: Callable[[], DocumentRecipe],
) -> DocumentRecipe:
    if template_spec:
        return template_spec.to_recipe()
    return default_recipe_builder()
