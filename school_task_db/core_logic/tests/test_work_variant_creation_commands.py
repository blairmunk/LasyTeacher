from unittest import TestCase

from core_logic.entities.work_specification_commands import CreateWorkParams
from core_logic.entities.work_variant_composition import VariantCreationPlan
from core_logic.entities.work_variant_creation_commands import (
    CreatedWorkWithVariantsRef,
    CreateWorkWithVariantsParams,
    NewWorkVariantParams,
)


class WorkVariantCreationCommandTests(TestCase):
    def test_command_collections_copy_mutable_inputs(self):
        task_plans = []
        content_blocks = []
        plan = VariantCreationPlan(
            number=1,
            work_name_snapshot='Работа над ошибками',
            max_score_snapshot=0,
            duration_snapshot=45,
            tasks=task_plans,
            content_blocks=content_blocks,
        )
        variants = [NewWorkVariantParams(student_id='student-1', plan=plan)]
        params = CreateWorkWithVariantsParams(
            work=CreateWorkParams(name='Работа над ошибками'),
            variants=variants,
        )
        variant_ids = ['variant-1']
        created = CreatedWorkWithVariantsRef(
            work_id='work-1',
            variant_ids=variant_ids,
        )

        task_plans.append(object())
        content_blocks.append(object())
        variants.clear()
        variant_ids.clear()

        self.assertEqual(plan.tasks, ())
        self.assertEqual(plan.content_blocks, ())
        self.assertEqual(len(params.variants), 1)
        self.assertEqual(created.variant_ids, ('variant-1',))
