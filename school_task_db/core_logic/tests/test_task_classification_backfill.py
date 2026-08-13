from unittest import TestCase

from core_logic.entities.task_classification_backfill import (
    BackfillContentEntryRef,
    BackfillRequirementRef,
    BackfillTaskRef,
    TaskClassificationBackfillSnapshot,
)
from core_logic.services.task_classification_backfill_planner import (
    plan_task_classification_backfill,
)


class TaskClassificationBackfillPlannerTests(TestCase):
    def test_prefers_subtopic_and_uses_content_codifier_for_requirement(self):
        snapshot = TaskClassificationBackfillSnapshot(
            tasks=(BackfillTaskRef(
                pk='task-1',
                topic_id='topic-1',
                subtopic_id='subtopic-1',
                legacy_content_code='1.1',
                legacy_requirement_code='2.1',
            ),),
            content_entries=(
                BackfillContentEntryRef(
                    pk='oge-entry',
                    codifier_id='oge',
                    code='1.1',
                    topic_id='topic-1',
                    subtopic_id='subtopic-1',
                ),
                BackfillContentEntryRef(
                    pk='ege-entry',
                    codifier_id='ege',
                    code='1.1',
                    topic_id='topic-1',
                    subtopic_id='subtopic-2',
                ),
            ),
            requirements=(
                BackfillRequirementRef('oge-req', 'oge', '2.1'),
                BackfillRequirementRef('ege-req', 'ege', '2.1'),
            ),
        )

        plan = plan_task_classification_backfill(snapshot)

        self.assertEqual(len(plan.mutations), 2)
        self.assertEqual(plan.mutations[0].target_id, 'oge-entry')
        self.assertEqual(plan.mutations[0].reason, 'subtopic')
        self.assertEqual(plan.mutations[1].target_id, 'oge-req')
        self.assertEqual(plan.issues, ())

    def test_reports_ambiguous_and_unresolved_candidates(self):
        snapshot = TaskClassificationBackfillSnapshot(
            tasks=(
                BackfillTaskRef(
                    pk='ambiguous',
                    topic_id='topic',
                    legacy_content_code='1.1',
                ),
                BackfillTaskRef(
                    pk='missing',
                    topic_id='topic',
                    legacy_content_code='9.9',
                ),
            ),
            content_entries=(
                BackfillContentEntryRef('first', 'oge', '1.1'),
                BackfillContentEntryRef('second', 'ege', '1.1'),
            ),
            requirements=(),
        )

        plan = plan_task_classification_backfill(snapshot)

        self.assertEqual(plan.mutations, ())
        self.assertEqual(plan.issues[0].status, 'ambiguous')
        self.assertEqual(plan.issues[1].status, 'unresolved')

    def test_skips_relations_that_are_already_explicit(self):
        snapshot = TaskClassificationBackfillSnapshot(
            tasks=(BackfillTaskRef(
                pk='task-1',
                topic_id='topic',
                legacy_content_code='1.1',
                content_entry_ids=('existing',),
                content_codifier_ids=('oge',),
            ),),
            content_entries=(
                BackfillContentEntryRef('existing', 'oge', '1.1'),
            ),
            requirements=(),
        )

        plan = plan_task_classification_backfill(snapshot)

        self.assertEqual(plan.mutations, ())
        self.assertEqual(plan.issues, ())

    def test_reports_mismatch_for_incompatible_explicit_relation(self):
        snapshot = TaskClassificationBackfillSnapshot(
            tasks=(BackfillTaskRef(
                pk='task-1',
                topic_id='topic',
                legacy_content_code='1.1',
                content_entry_ids=('existing',),
                content_codifier_ids=('oge',),
            ),),
            content_entries=(
                BackfillContentEntryRef('existing', 'oge', '9.9'),
            ),
            requirements=(),
        )

        plan = plan_task_classification_backfill(snapshot)

        self.assertEqual(plan.mutations, ())
        self.assertEqual(plan.issues[0].status, 'mismatch')
        self.assertEqual(plan.issues[0].candidate_ids, ('existing',))
