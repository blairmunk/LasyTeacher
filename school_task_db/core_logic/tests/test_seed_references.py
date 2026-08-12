from contextlib import contextmanager
from unittest import TestCase

from core_logic.entities.reference_seed import (
    ReferenceSeedDefinition,
    ReferenceSeedMutation,
    ReferenceSeedValidationError,
    SeedReferencesRequest,
    SimpleReferenceSeedItem,
    SubjectReferenceSeedItem,
)
from core_logic.use_cases.seed_references import SeedReferencesUseCase


def _definition():
    return ReferenceSeedDefinition(
        simple_references=(
            SimpleReferenceSeedItem('subjects', 'Физика\nМатематика'),
        ),
        subject_references=(
            SubjectReferenceSeedItem(
                subject='Физика',
                grade_level='7-9',
                category='content_elements',
                items_text='1.1|Механика',
            ),
        ),
    )


class _Repo:
    def __init__(self):
        self.calls = []

    def seed_simple_reference(self, item, replace_existing):
        self.calls.append(('simple', item, replace_existing))
        return ReferenceSeedMutation(
            reference_type='simple',
            key=(item.category,),
            display_name=item.category,
            status='created',
            items_count=2,
        )

    def seed_subject_reference(self, item, replace_existing):
        self.calls.append(('subject', item, replace_existing))
        return ReferenceSeedMutation(
            reference_type='subject',
            key=(item.subject, item.grade_level, item.category),
            display_name=item.subject,
            status='skipped',
            items_count=1,
        )


class _TransactionManager:
    @contextmanager
    def atomic(self):
        yield


class SeedReferencesUseCaseTests(TestCase):
    def test_seeds_all_definition_items_and_summarizes_statuses(self):
        repo = _Repo()

        result = SeedReferencesUseCase(repo, _TransactionManager()).execute(
            SeedReferencesRequest(
                definition=_definition(),
                replace_existing=True,
            ),
        )

        self.assertEqual(len(repo.calls), 2)
        self.assertTrue(all(call[2] for call in repo.calls))
        self.assertEqual(result.created_count, 1)
        self.assertEqual(result.updated_count, 0)
        self.assertEqual(result.skipped_count, 1)

    def test_rejects_duplicate_subject_reference_identity(self):
        item = _definition().subject_references[0]
        definition = ReferenceSeedDefinition(
            subject_references=(item, item),
        )

        with self.assertRaisesRegex(
            ReferenceSeedValidationError,
            'Повторяется предметный справочник',
        ):
            SeedReferencesUseCase(
                _Repo(),
                _TransactionManager(),
            ).execute(SeedReferencesRequest(definition=definition))
