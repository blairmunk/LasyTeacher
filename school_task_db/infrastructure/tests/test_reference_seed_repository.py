from django.test import TestCase

from core_logic.entities.reference_seed import (
    ReferenceSeedDefinition,
    SeedReferencesRequest,
    SimpleReferenceSeedItem,
    SubjectReferenceSeedItem,
)
from infrastructure.container import Container
from infrastructure.repositories.django_reference_seed_repo import (
    DjangoReferenceSeedRepository,
)
from references.models import SimpleReference, SubjectReference


def _definition(simple_text='Физика', subject_text='1.1|Механика'):
    return ReferenceSeedDefinition(
        simple_references=(
            SimpleReferenceSeedItem('subjects', simple_text),
        ),
        subject_references=(
            SubjectReferenceSeedItem(
                subject='Физика',
                grade_level='7-9',
                category='content_elements',
                items_text=subject_text,
            ),
        ),
    )


class DjangoReferenceSeedRepositoryTests(TestCase):
    def test_container_creates_complete_seed(self):
        result = Container().seed_references_use_case().execute(
            SeedReferencesRequest(definition=_definition()),
        )

        self.assertEqual(result.created_count, 2)
        self.assertEqual(result.updated_count, 0)
        self.assertEqual(SimpleReference.objects.get().get_items_list(), [
            'Физика',
        ])
        self.assertEqual(SubjectReference.objects.get().get_items_dict(), {
            '1.1': 'Механика',
        })

    def test_existing_seed_is_skipped_without_replace(self):
        use_case = Container().seed_references_use_case()
        use_case.execute(SeedReferencesRequest(definition=_definition()))

        result = use_case.execute(SeedReferencesRequest(
            definition=_definition('Математика', '2.1|Теплота'),
        ))

        self.assertEqual(result.skipped_count, 2)
        self.assertEqual(SimpleReference.objects.get().items_text, 'Физика')
        self.assertIn('1.1', SubjectReference.objects.get().items_text)

    def test_replace_updates_rows_without_changing_identity(self):
        use_case = Container().seed_references_use_case()
        use_case.execute(SeedReferencesRequest(definition=_definition()))
        simple_pk = SimpleReference.objects.get().pk
        subject_pk = SubjectReference.objects.get().pk

        result = use_case.execute(SeedReferencesRequest(
            definition=_definition('Математика', '2.1|Теплота'),
            replace_existing=True,
        ))

        self.assertEqual(result.updated_count, 2)
        self.assertEqual(SimpleReference.objects.get().pk, simple_pk)
        self.assertEqual(SubjectReference.objects.get().pk, subject_pk)
        self.assertEqual(SimpleReference.objects.get().items_text, 'Математика')
        self.assertIn('2.1', SubjectReference.objects.get().items_text)

    def test_container_wires_reference_seed_adapter(self):
        use_case = Container().seed_references_use_case()

        self.assertIsInstance(
            use_case.reference_repo,
            DjangoReferenceSeedRepository,
        )
