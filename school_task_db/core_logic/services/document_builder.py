"""Pure document builders."""

from core_logic.interfaces.document_building import (
    IDocumentSectionPayloadBuilder,
)
from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSection,
    DocumentSourceRef,
)
from core_logic.interfaces.document_rendering import IDocumentBuilder
from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)


class UnsupportedDocumentSectionPayloadBuilder(ValueError):
    pass


class DocumentSectionPayloadBuilderRegistry:
    def __init__(self):
        self._builders = {}

    def register(
        self,
        section_type: str,
        builder: IDocumentSectionPayloadBuilder,
        document_type: str = '',
        source_type: str = '',
    ) -> None:
        if not section_type:
            raise ValueError('section_type is required')
        self._builders[(source_type, document_type, section_type)] = builder

    def extend(self, registry: "DocumentSectionPayloadBuilderRegistry") -> None:
        self._builders.update(registry._builders)

    def get(
        self,
        section_type: str,
        document_type: str = '',
        source_type: str = '',
    ) -> IDocumentSectionPayloadBuilder:
        for key in (
            (source_type, document_type, section_type),
            ('', document_type, section_type),
            (source_type, '', section_type),
            ('', '', section_type),
        ):
            if key in self._builders:
                return self._builders[key]
        raise UnsupportedDocumentSectionPayloadBuilder(
            f'{source_type}:{document_type}:{section_type}',
        )

    def build_payload(
        self,
        request: DocumentSectionPayloadBuildRequest,
    ):
        builder = self.get(
            section_type=request.section.section_type,
            document_type=request.recipe.document_type,
            source_type=request.source.source_type,
        )
        return builder.build_payload(request)


class RecipeDocumentBuilder(IDocumentBuilder):
    def __init__(self, section_payload_builder_registry=None):
        self.section_payload_builder_registry = section_payload_builder_registry

    def build(
        self,
        source: DocumentSourceRef,
        recipe: DocumentRecipe,
    ) -> Document:
        return Document(
            title=source.title,
            document_type=recipe.document_type,
            source=source,
            sections=[
                DocumentSection(
                    section_type=section.section_type,
                    title=section.title,
                    payload=self._section_payload(source, recipe, section),
                )
                for section in recipe.sections
            ],
        )

    def _section_payload(self, source, recipe, section):
        if self.section_payload_builder_registry is None:
            return dict(section.options)

        try:
            return dict(
                self.section_payload_builder_registry.build_payload(
                    DocumentSectionPayloadBuildRequest(
                        source=source,
                        recipe=recipe,
                        section=section,
                    )
                )
            )
        except UnsupportedDocumentSectionPayloadBuilder:
            return dict(section.options)
