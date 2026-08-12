from contextlib import contextmanager
from unittest import TestCase

from core_logic.entities.curriculum_import import (
    CodifierContentBindingItem,
    CurriculumImportDefinition,
    CurriculumImportRequest,
    CurriculumImportResult,
    CurriculumImportValidationError,
    CurriculumSubtopicImportItem,
    CurriculumTopicImportItem,
)
from core_logic.use_cases.import_curriculum import ImportCurriculumUseCase


def _definition(bindings=None):
    return CurriculumImportDefinition(
        subject='Физика',
        sections=('Механика',),
        topics=(
            CurriculumTopicImportItem(
                section='Механика',
                name='Кинематика',
                grade_level=9,
                order=1,
                subtopics=(
                    CurriculumSubtopicImportItem(
                        name='Скорость',
                        order=1,
                    ),
                ),
            ),
        ),
        bindings=bindings or (
            CodifierContentBindingItem(
                codifier_short_name='ОГЭ 2026',
                content_code='1.1',
                topic_name='Кинематика',
                subtopic_name='Скорость',
            ),
        ),
    )


class _Repo:
    def __init__(self):
        self.received = None

    def apply_curriculum_import(self, definition, clear_existing):
        self.received = (definition, clear_existing)
        return CurriculumImportResult(topics_created=1)


class _TransactionManager:
    def __init__(self):
        self.entered = 0

    @contextmanager
    def atomic(self):
        self.entered += 1
        yield


class ImportCurriculumUseCaseTests(TestCase):
    def test_applies_validated_definition_in_transaction(self):
        repo = _Repo()
        transaction_manager = _TransactionManager()

        result = ImportCurriculumUseCase(repo, transaction_manager).execute(
            CurriculumImportRequest(
                definition=_definition(),
                clear_existing=True,
            ),
        )

        self.assertEqual(result.topics_created, 1)
        self.assertEqual(repo.received, (_definition(), True))
        self.assertEqual(transaction_manager.entered, 1)

    def test_rejects_binding_to_unknown_topic(self):
        definition = _definition(bindings=(
            CodifierContentBindingItem(
                codifier_short_name='ОГЭ 2026',
                content_code='1.1',
                topic_name='Неизвестная тема',
            ),
        ))

        with self.assertRaisesRegex(
            CurriculumImportValidationError,
            'Тема привязки не объявлена',
        ):
            ImportCurriculumUseCase(
                _Repo(),
                _TransactionManager(),
            ).execute(CurriculumImportRequest(definition=definition))

    def test_rejects_subtopic_owned_by_another_topic(self):
        definition = CurriculumImportDefinition(
            subject='Физика',
            sections=('Механика',),
            topics=(
                CurriculumTopicImportItem(
                    section='Механика',
                    name='Кинематика',
                    grade_level=9,
                    order=1,
                    subtopics=(CurriculumSubtopicImportItem('Скорость', 1),),
                ),
                CurriculumTopicImportItem(
                    section='Механика',
                    name='Динамика',
                    grade_level=9,
                    order=2,
                ),
            ),
            bindings=(
                CodifierContentBindingItem(
                    codifier_short_name='ОГЭ 2026',
                    content_code='1.1',
                    topic_name='Динамика',
                    subtopic_name='Скорость',
                ),
            ),
        )

        with self.assertRaisesRegex(
            CurriculumImportValidationError,
            'не относится к теме',
        ):
            ImportCurriculumUseCase(
                _Repo(),
                _TransactionManager(),
            ).execute(CurriculumImportRequest(definition=definition))
