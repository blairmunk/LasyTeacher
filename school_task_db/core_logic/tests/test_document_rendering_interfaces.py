from unittest import TestCase

from core_logic.entities.document import (
    Document,
    DocumentRecipe,
    DocumentSection,
    DocumentSectionSpec,
    DocumentSourceRef,
)
from core_logic.entities.document_rendering import GeneratedDocument
from core_logic.interfaces.document_engine import IDocumentEngine
from core_logic.interfaces.document_building import (
    IDocumentSectionPayloadBuilder,
)
from core_logic.interfaces.document_rendering import (
    IDocumentContentWrapper,
    IDocumentBuilder,
    IDocumentRenderer,
    IDocumentSectionRenderer,
)
from core_logic.value_objects.content_config import RenderTarget
from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)
from core_logic.value_objects.document_render_plan import (
    DocumentContentWrapRequest,
    DocumentRenderRequest,
    DocumentSectionRenderRequest,
)


class FakeDocumentBuilder(IDocumentBuilder):
    def __init__(self):
        self.request = None

    def build(self, source, recipe, render_target=None):
        self.request = (source, recipe, render_target)
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

    def render(self, request):
        self.request = request
        return GeneratedDocument(
            file_type=request.render_target.renderer_type,
        )


class FakeDocumentSectionRenderer(IDocumentSectionRenderer):
    def __init__(self):
        self.request = None

    def render_section(self, request):
        self.request = request
        return f'<section>{request.section.section_type}</section>'


class FakeSectionPayloadBuilder(IDocumentSectionPayloadBuilder):
    def __init__(self):
        self.request = None

    def build_payload(self, request):
        self.request = request
        return {'section_type': request.section.section_type}


class FakeDocumentContentWrapper(IDocumentContentWrapper):
    def __init__(self):
        self.request = None

    def wrap_content(self, request):
        self.request = request
        return f'<html>{request.body_content}</html>'


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

        self.assertEqual(builder.request, (source, recipe, None))
        self.assertEqual(document.title, 'Контрольная')
        self.assertEqual(document.section_types, ('tasks',))

    def test_document_renderer_contract_accepts_document_and_target(self):
        renderer = FakeDocumentRenderer()
        document = Document(title='Контрольная')
        target = RenderTarget(renderer_type='html')
        request = DocumentRenderRequest(
            document=document,
            render_target=target,
        )

        result = renderer.render(request)

        self.assertEqual(renderer.request, request)
        self.assertEqual(result.file_type, 'html')

    def test_document_section_renderer_contract_accepts_section_request(self):
        renderer = FakeDocumentSectionRenderer()
        document = Document(title='Контрольная')
        section = DocumentSection(section_type='task_list')
        target = RenderTarget(renderer_type='html')
        request = DocumentSectionRenderRequest(
            document=document,
            section=section,
            render_target=target,
        )

        result = renderer.render_section(request)

        self.assertEqual(renderer.request, request)
        self.assertEqual(result, '<section>task_list</section>')

    def test_document_section_payload_builder_contract_accepts_build_request(self):
        builder = FakeSectionPayloadBuilder()
        source = DocumentSourceRef(source_type='work')
        recipe = DocumentRecipe(
            document_type='work',
            sections=[DocumentSectionSpec(section_type='task_list')],
        )
        request = DocumentSectionPayloadBuildRequest(
            source=source,
            recipe=recipe,
            section=recipe.sections[0],
        )

        payload = builder.build_payload(request)

        self.assertEqual(builder.request, request)
        self.assertEqual(payload, {'section_type': 'task_list'})

    def test_document_content_wrapper_contract_accepts_wrap_request(self):
        wrapper = FakeDocumentContentWrapper()
        document = Document(title='Контрольная')
        target = RenderTarget(renderer_type='html')
        request = DocumentContentWrapRequest(
            document=document,
            render_target=target,
            body_content='<section>body</section>',
        )

        content = wrapper.wrap_content(request)

        self.assertEqual(wrapper.request, request)
        self.assertEqual(content, '<html><section>body</section></html>')
