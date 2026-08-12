from django.test import TestCase

from codifier.models import CodifierSpec, ContentEntry, Requirement
from core_logic.entities.codifier_import import (
    CodifierImportContentItem,
    CodifierImportDefinition,
    CodifierImportRequirementItem,
    ImportCodifierRequest,
)
from infrastructure.container import Container
from infrastructure.repositories.django_codifier_import_repo import (
    DjangoCodifierImportRepository,
)


def _definition(name='ОГЭ 2026'):
    return CodifierImportDefinition(
        name=f'Кодификатор {name} по физике',
        short_name=name,
        subject='Физика',
        exam_type='oge',
        year=2026,
        content=(
            CodifierImportContentItem(code='1', name='Механика'),
            CodifierImportContentItem(
                code='1.1',
                name='Кинематика',
                parent_code='1',
                grade_studied='7, 9',
            ),
        ),
        requirements=(
            CodifierImportRequirementItem(
                code='1',
                name='Знать основные понятия',
                cognitive_level='know',
            ),
        ),
    )


class DjangoCodifierImportRepositoryTests(TestCase):
    def test_container_imports_complete_codifier_hierarchy(self):
        container = Container()

        result = container.import_codifier_use_case().execute(
            ImportCodifierRequest(definition=_definition()),
        )

        codifier = CodifierSpec.objects.get()
        root = ContentEntry.objects.get(code='1')
        child = ContentEntry.objects.get(code='1.1')
        requirement = Requirement.objects.get()
        self.assertEqual(result.status, 'imported')
        self.assertEqual(result.content_count, 2)
        self.assertEqual(child.parent, root)
        self.assertEqual(child.grade_studied, '7, 9')
        self.assertEqual(requirement.codifier, codifier)
        self.assertEqual(requirement.cognitive_level, 'know')

    def test_existing_codifier_is_not_replaced_without_clear(self):
        container = Container()
        use_case = container.import_codifier_use_case()
        use_case.execute(ImportCodifierRequest(definition=_definition()))

        result = use_case.execute(
            ImportCodifierRequest(definition=_definition('Другое имя')),
        )

        self.assertEqual(result.status, 'already_exists')
        self.assertEqual(CodifierSpec.objects.get().short_name, 'ОГЭ 2026')

    def test_clear_replaces_existing_codifier_tree(self):
        container = Container()
        use_case = container.import_codifier_use_case()
        use_case.execute(ImportCodifierRequest(definition=_definition()))

        result = use_case.execute(ImportCodifierRequest(
            definition=_definition('Новое имя'),
            clear_existing=True,
        ))

        self.assertEqual(result.status, 'imported')
        self.assertGreaterEqual(result.deleted_count, 4)
        self.assertEqual(CodifierSpec.objects.get().short_name, 'Новое имя')

    def test_container_wires_codifier_import_adapter(self):
        use_case = Container().import_codifier_use_case()

        self.assertIsInstance(
            use_case.codifier_repo,
            DjangoCodifierImportRepository,
        )
