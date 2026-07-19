"""Pure document builders."""

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSection,
    DocumentSourceRef,
)
from core_logic.interfaces.document_rendering import IDocumentBuilder


class RecipeDocumentBuilder(IDocumentBuilder):
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
                    payload=dict(section.options),
                )
                for section in recipe.sections
            ],
        )
