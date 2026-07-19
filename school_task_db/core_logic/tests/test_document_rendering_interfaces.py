from unittest import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSection,
    DocumentSectionSpec,
    DocumentSourceRef,
)
from core_logic.entities.document_generation import GeneratedDocument
from core_logic.interfaces.document_rendering import (
    IDocumentBuilder,
    IDocumentRenderer,
)
from core_logic.value_objects.content_config import RenderTarget


class FakeDocumentBuilder(IDocumentBuilder):
    def __init__(self):
        self.request = None

    def build(self, source, recipe):
        self.request = (source, recipe)
        return Document(
            title=source.title,
            source=source,
            sections=[
                DocumentSection(section_type=section.section_type)
                for section in recipe.sections
            ],
        )


class FakeDocumentRenderer(IDocumentRenderer):
    def __init__(self):
        self.request = None

    def render(self, document, render_target):
        self.request = (document, render_target)
        return GeneratedDocument(file_type=render_target.renderer_type)


class DocumentRenderingInterfaceTests(TestCase):
    def test_document_builder_contract_accepts_source_and_recipe(self):
        builder = FakeDocumentBuilder()
        source = DocumentSourceRef(
            source_type='work',
            source_id='work-1',
            title='Контрольная',
        )
        recipe = DocumentRecipe(
            document_type='work',
            sections=[DocumentSectionSpec(section_type='tasks')],
        )

        document = builder.build(source, recipe)

        self.assertEqual(builder.request, (source, recipe))
        self.assertEqual(document.title, 'Контрольная')
        self.assertEqual(document.section_types, ('tasks',))

    def test_document_renderer_contract_accepts_document_and_target(self):
        renderer = FakeDocumentRenderer()
        document = Document(title='Контрольная')
        target = RenderTarget(renderer_type='html')

        result = renderer.render(document, target)

        self.assertEqual(renderer.request, (document, target))
        self.assertEqual(result.file_type, 'html')
