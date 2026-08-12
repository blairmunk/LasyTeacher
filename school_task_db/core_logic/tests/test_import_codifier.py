from contextlib import contextmanager
from unittest import TestCase

from core_logic.entities.codifier_import import (
    CodifierImportContentItem,
    CodifierImportDefinition,
    CodifierImportRequirementItem,
    CodifierImportValidationError,
    ImportCodifierRequest,
)
from core_logic.use_cases.import_codifier import ImportCodifierUseCase


def _definition(content=None):
    return CodifierImportDefinition(
        name='Кодификатор ОГЭ 2026 по физике',
        short_name='ОГЭ 2026',
        subject='Физика',
        exam_type='oge',
        year=2026,
        content=content or (
            CodifierImportContentItem(code='1', name='Механика'),
            CodifierImportContentItem(
                code='1.1',
                name='Кинематика',
                parent_code='1',
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


class _Repo:
    def __init__(self, exists=False):
        self.exists = exists
        self.deleted = 0
        self.created = None

    def codifier_exists(self, exam_type, year, subject):
        return self.exists

    def delete_codifier(self, exam_type, year, subject):
        self.deleted += 3
        self.exists = False
        return 3

    def create_codifier(self, definition):
        self.created = definition
        self.exists = True
        return definition.short_name


class _TransactionManager:
    def __init__(self):
        self.entered = 0

    @contextmanager
    def atomic(self):
        self.entered += 1
        yield


class ImportCodifierUseCaseTests(TestCase):
    def test_imports_valid_definition(self):
        repo = _Repo()
        transaction_manager = _TransactionManager()

        result = ImportCodifierUseCase(repo, transaction_manager).execute(
            ImportCodifierRequest(definition=_definition()),
        )

        self.assertEqual(result.status, 'imported')
        self.assertEqual(result.display_name, 'ОГЭ 2026')
        self.assertEqual(result.content_count, 2)
        self.assertEqual(result.requirements_count, 1)
        self.assertIsNotNone(repo.created)
        self.assertEqual(transaction_manager.entered, 1)

    def test_reports_existing_codifier_without_replacing_it(self):
        repo = _Repo(exists=True)

        result = ImportCodifierUseCase(
            repo,
            _TransactionManager(),
        ).execute(ImportCodifierRequest(definition=_definition()))

        self.assertEqual(result.status, 'already_exists')
        self.assertIsNone(repo.created)

    def test_clear_deletes_existing_tree_before_import(self):
        repo = _Repo(exists=True)

        result = ImportCodifierUseCase(
            repo,
            _TransactionManager(),
        ).execute(
            ImportCodifierRequest(
                definition=_definition(),
                clear_existing=True,
            ),
        )

        self.assertEqual(result.status, 'imported')
        self.assertEqual(result.deleted_count, 3)
        self.assertIsNotNone(repo.created)

    def test_rejects_parent_declared_after_child(self):
        definition = _definition(content=(
            CodifierImportContentItem(
                code='1.1',
                name='Кинематика',
                parent_code='1',
            ),
            CodifierImportContentItem(code='1', name='Механика'),
        ))

        with self.assertRaisesRegex(
            CodifierImportValidationError,
            'должен быть объявлен раньше',
        ):
            ImportCodifierUseCase(
                _Repo(),
                _TransactionManager(),
            ).execute(ImportCodifierRequest(definition=definition))
