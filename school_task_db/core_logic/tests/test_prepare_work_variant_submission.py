from unittest import TestCase

from core_logic.use_cases.bulk_delete_variants import BulkDeleteVariantsRequest
from core_logic.use_cases.create_work_from_orphans import CreateWorkFromOrphansRequest
from core_logic.use_cases.delete_variant import DeleteVariantRequest
from core_logic.use_cases.prepare_work_variant_submission import (
    PrepareBulkDeleteVariantsSubmissionUseCase,
    PrepareCreateWorkFromOrphansSubmissionUseCase,
    PrepareDeleteVariantSubmissionUseCase,
    PrepareVariantActionSubmissionRequest,
)


class PrepareWorkVariantSubmissionUseCaseTests(TestCase):
    def test_prepare_delete_variant_submission(self):
        result = PrepareDeleteVariantSubmissionUseCase().execute(
            PrepareVariantActionSubmissionRequest(
                variant_id='variant-1',
                data={'action': ['detach']},
            )
        )

        self.assertEqual(
            result,
            DeleteVariantRequest(variant_id='variant-1', action='detach'),
        )

    def test_prepare_delete_variant_submission_uses_delete_default(self):
        result = PrepareDeleteVariantSubmissionUseCase().execute(
            PrepareVariantActionSubmissionRequest(
                variant_id='variant-1',
                data={},
            )
        )

        self.assertEqual(result.action, 'delete')

    def test_prepare_bulk_delete_variants_submission(self):
        result = PrepareBulkDeleteVariantsSubmissionUseCase().execute(
            PrepareVariantActionSubmissionRequest(
                work_id='work-1',
                data={'variant_ids': ['variant-1', 'variant-2']},
            )
        )

        self.assertEqual(
            result,
            BulkDeleteVariantsRequest(
                work_id='work-1',
                variant_ids=['variant-1', 'variant-2'],
            ),
        )

    def test_prepare_create_work_from_orphans_submission(self):
        result = PrepareCreateWorkFromOrphansSubmissionUseCase().execute(
            PrepareVariantActionSubmissionRequest(
                data={
                    'variant_ids': ['variant-1', 'variant-2'],
                    'work_name': ['Работа из сирот'],
                },
            )
        )

        self.assertEqual(
            result,
            CreateWorkFromOrphansRequest(
                variant_ids=['variant-1', 'variant-2'],
                work_name='Работа из сирот',
            ),
        )
