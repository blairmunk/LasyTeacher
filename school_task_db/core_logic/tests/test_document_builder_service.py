from unittest import TestCase

from core_logic.entities.document import (
    DocumentPresentation,
    DocumentRecipe,
    DocumentSectionSpec,
    DocumentSourceRef,
)
from core_logic.services.document_builder import (
    DocumentSectionPayloadBuilderRegistry,
    RecipeDocumentBuilder,
    UnsupportedDocumentSectionPayloadBuilder,
)
from core_logic.value_objects.document_build_plan import (
    DocumentSectionPayloadBuildRequest,
)
from core_logic.value_objects.document_render_options import RenderTarget


class RecipeDocumentBuilderTests(TestCase):
    def test_builds_document_from_source_and_recipe(self):
        builder = RecipeDocumentBuilder()
        source = DocumentSourceRef(
            source_type='work',
            source_id='work-1',
            title='Контрольная',
        )
        recipe = DocumentRecipe(
            document_type='work',
            sections=[
                DocumentSectionSpec(
                    section_type='tasks',
                    title='Задания',
                    options={'include_hints': True},
                ),
                DocumentSectionSpec(section_type='answers'),
            ],
        )

        document = builder.build(source, recipe)

        self.assertEqual(document.title, 'Контрольная')
        self.assertEqual(document.document_type, 'work')
        self.assertEqual(document.source, source)
        self.assertEqual(document.section_types, ('tasks', 'answers'))
        self.assertEqual(document.sections[0].title, 'Задания')
        self.assertEqual(document.sections[0].payload, {'include_hints': True})

    def test_copies_recipe_presentation_to_document(self):
        builder = RecipeDocumentBuilder()
        presentation = DocumentPresentation(
            custom_latex_preamble='\\usepackage{multicol}',
        )
        source = DocumentSourceRef(source_type='work')
        recipe = DocumentRecipe(
            document_type='work',
            sections=[DocumentSectionSpec(section_type='header')],
            presentation=presentation,
        )

        document = builder.build(source, recipe)

        self.assertEqual(document.presentation, presentation)

    def test_copies_section_options_into_payload(self):
        builder = RecipeDocumentBuilder()
        options = {'include_scores': True}
        source = DocumentSourceRef(source_type='remedial_variant')
        recipe = DocumentRecipe(
            document_type='remedial_sheet',
            sections=[
                DocumentSectionSpec(
                    section_type='original_mistakes',
                    options=options,
                ),
            ],
        )

        document = builder.build(source, recipe)
        options['include_scores'] = False

        self.assertEqual(
            document.sections[0].payload,
            {'include_scores': True},
        )

    def test_uses_registered_section_payload_builder(self):
        registry = DocumentSectionPayloadBuilderRegistry()
        payload_builder = FakeSectionPayloadBuilder(
            payload={'tasks': ['task-1']},
        )
        registry.register('task_list', payload_builder, document_type='work')
        builder = RecipeDocumentBuilder(
            section_payload_builder_registry=registry,
        )
        source = DocumentSourceRef(
            source_type='work',
            source_id='work-1',
            title='Контрольная',
        )
        recipe = DocumentRecipe(
            document_type='work',
            sections=[
                DocumentSectionSpec(
                    section_type='task_list',
                    options={'include_hints': True},
                ),
            ],
        )

        document = builder.build(source, recipe)

        self.assertEqual(document.sections[0].payload, {'tasks': ['task-1']})
        self.assertEqual(payload_builder.request.source, source)
        self.assertEqual(payload_builder.request.recipe, recipe)
        self.assertEqual(payload_builder.request.section, recipe.sections[0])
        self.assertIsNone(payload_builder.request.render_target)

    def test_passes_render_target_to_section_payload_builder(self):
        registry = DocumentSectionPayloadBuilderRegistry()
        payload_builder = FakeSectionPayloadBuilder(payload={'tasks': []})
        registry.register('task_list', payload_builder, document_type='work')
        builder = RecipeDocumentBuilder(
            section_payload_builder_registry=registry,
        )
        source = DocumentSourceRef(source_type='work', source_id='work-1')
        recipe = DocumentRecipe(
            document_type='work',
            sections=[DocumentSectionSpec(section_type='task_list')],
        )
        render_target = RenderTarget(renderer_type='latex')

        builder.build(source, recipe, render_target=render_target)

        self.assertEqual(payload_builder.request.render_target, render_target)

    def test_keeps_section_options_for_unregistered_payload_builder(self):
        builder = RecipeDocumentBuilder(
            section_payload_builder_registry=DocumentSectionPayloadBuilderRegistry(),
        )
        source = DocumentSourceRef(source_type='work')
        recipe = DocumentRecipe(
            document_type='work',
            sections=[
                DocumentSectionSpec(
                    section_type='task_list',
                    options={'include_hints': True},
                ),
            ],
        )

        document = builder.build(source, recipe)

        self.assertEqual(
            document.sections[0].payload,
            {'include_hints': True},
        )


class DocumentSectionPayloadBuilderRegistryTests(TestCase):
    def test_registers_and_delegates_to_payload_builder(self):
        registry = DocumentSectionPayloadBuilderRegistry()
        builder = FakeSectionPayloadBuilder(payload={'title': 'Контрольная'})
        registry.register('header', builder)
        source = DocumentSourceRef(source_type='work')
        recipe = DocumentRecipe(
            document_type='work',
            sections=[DocumentSectionSpec(section_type='header')],
        )

        payload = registry.build_payload(
            request=payload_build_request(source, recipe, recipe.sections[0]),
        )

        self.assertEqual(payload, {'title': 'Контрольная'})
        self.assertEqual(builder.request.section.section_type, 'header')

    def test_prefers_exact_payload_builder_key(self):
        registry = DocumentSectionPayloadBuilderRegistry()
        common_builder = FakeSectionPayloadBuilder(payload={'title': 'Common'})
        exact_builder = FakeSectionPayloadBuilder(payload={'title': 'Exact'})
        registry.register('header', common_builder)
        registry.register(
            'header',
            exact_builder,
            document_type='work',
            source_type='work',
        )
        source = DocumentSourceRef(source_type='work')
        recipe = DocumentRecipe(
            document_type='work',
            sections=[DocumentSectionSpec(section_type='header')],
        )

        payload = registry.build_payload(
            payload_build_request(source, recipe, recipe.sections[0]),
        )

        self.assertEqual(payload, {'title': 'Exact'})
        self.assertIsNone(common_builder.request)

    def test_extends_from_another_payload_builder_registry(self):
        registry = DocumentSectionPayloadBuilderRegistry()
        other_registry = DocumentSectionPayloadBuilderRegistry()
        builder = FakeSectionPayloadBuilder(payload={'tasks': []})
        other_registry.register('task_list', builder, document_type='work')
        source = DocumentSourceRef(source_type='work')
        recipe = DocumentRecipe(
            document_type='work',
            sections=[DocumentSectionSpec(section_type='task_list')],
        )

        registry.extend(other_registry)

        payload = registry.build_payload(
            payload_build_request(source, recipe, recipe.sections[0]),
        )

        self.assertEqual(payload, {'tasks': []})

    def test_rejects_empty_section_type(self):
        registry = DocumentSectionPayloadBuilderRegistry()

        with self.assertRaises(ValueError):
            registry.register('', FakeSectionPayloadBuilder())

    def test_rejects_unsupported_payload_builder(self):
        registry = DocumentSectionPayloadBuilderRegistry()

        with self.assertRaises(UnsupportedDocumentSectionPayloadBuilder):
            registry.get('header', document_type='work', source_type='work')


class FakeSectionPayloadBuilder:
    def __init__(self, payload=None):
        self.payload = payload or {}
        self.request = None

    def build_payload(self, request):
        self.request = request
        return self.payload


def payload_build_request(source, recipe, section):
    return DocumentSectionPayloadBuildRequest(
        source=source,
        recipe=recipe,
        section=section,
    )
