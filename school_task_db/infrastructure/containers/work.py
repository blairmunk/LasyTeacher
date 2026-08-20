"""Work and variant wiring for the application dependency container."""

from core_logic.services.work_service import WorkService
from core_logic.use_cases.bulk_delete_variants import BulkDeleteVariantsUseCase
from core_logic.use_cases.compose_work_variants import ComposeWorkVariantsUseCase
from core_logic.use_cases.create_work_from_groups import (
    CreateWorkFromGroupsUseCase,
    PrepareCreateWorkFromGroupsSubmissionUseCase,
)
from core_logic.use_cases.create_work_from_orphans import (
    CreateWorkFromOrphansUseCase,
)
from core_logic.use_cases.create_work_from_tasks import CreateWorkFromTasksUseCase
from core_logic.use_cases.delete_variant import DeleteVariantUseCase
from core_logic.use_cases.get_orphan_variant_list import GetOrphanVariantListUseCase
from core_logic.use_cases.get_variant_delete_info import GetVariantDeleteInfoUseCase
from core_logic.use_cases.get_variant_detail import GetVariantDetailUseCase
from core_logic.use_cases.get_variant_generation_form import (
    GetVariantGenerationFormUseCase,
)
from core_logic.use_cases.get_variant_list import GetVariantListUseCase
from core_logic.use_cases.get_work_detail import GetWorkDetailUseCase
from core_logic.use_cases.get_work_form_data import GetWorkFormDataUseCase
from core_logic.use_cases.get_work_list import GetWorkListUseCase
from core_logic.use_cases.prepare_work_variant_submission import (
    PrepareBulkDeleteVariantsSubmissionUseCase,
    PrepareCreateWorkFromOrphansSubmissionUseCase,
    PrepareDeleteVariantSubmissionUseCase,
)
from core_logic.use_cases.save_work import (
    CreateWorkWithSpecificationUseCase,
    UpdateWorkWithSpecificationUseCase,
)
from core_logic.use_cases.sync_work_analog_groups import (
    SyncWorkAnalogGroupsUseCase,
)
from infrastructure.forms.work_forms import WorkFormAdapter
from infrastructure.repositories.django_orphan_variant_attachment_repo import (
    DjangoOrphanVariantAttachmentRepository,
)
from infrastructure.repositories.django_orphan_variant_catalog_repo import (
    DjangoOrphanVariantCatalogRepository,
)
from infrastructure.repositories.django_variant_generation_form_repo import (
    DjangoVariantGenerationFormRepository,
)
from infrastructure.repositories.django_variant_lifecycle_command_repo import (
    DjangoVariantLifecycleCommandRepository,
)
from infrastructure.repositories.django_variant_lifecycle_query_repo import (
    DjangoVariantLifecycleQueryRepository,
)
from infrastructure.repositories.django_variant_read_repo import (
    DjangoVariantReadRepository,
)
from infrastructure.repositories.django_work_read_repo import (
    DjangoWorkReadRepository,
)
from infrastructure.repositories.django_work_spec_sync_repo import (
    DjangoWorkSpecSyncRepository,
)
from infrastructure.repositories.django_work_specification_repo import (
    DjangoWorkSpecificationRepository,
)
from infrastructure.repositories.django_work_task_group_repo import (
    DjangoWorkTaskGroupRepository,
)
from infrastructure.repositories.django_work_variant_composition_repo import (
    DjangoWorkVariantCompositionRepository,
)
from infrastructure.repositories.django_work_variant_creation_repo import (
    DjangoWorkVariantCreationRepository,
)


class WorkCompositionMixin:
    """Owns work specifications and generated variant infrastructure wiring."""

    def _initialize_work_composition(self):
        self._work_task_group_repo = None
        self._work_specification_repo = None
        self._work_variant_creation_repo = None
        self._variant_generation_form_repo = None
        self._work_variant_composition_repo = None
        self._work_spec_sync_repo = None
        self._work_read_repo = None
        self._variant_read_repo = None
        self._variant_lifecycle_query_repo = None
        self._variant_lifecycle_command_repo = None
        self._orphan_variant_catalog_repo = None
        self._orphan_variant_attachment_repo = None
        self._work_form_adapter = None

    @property
    def work_task_group_repo(self):
        if self._work_task_group_repo is None:
            self._work_task_group_repo = DjangoWorkTaskGroupRepository()
        return self._work_task_group_repo

    @property
    def work_specification_repo(self):
        if self._work_specification_repo is None:
            self._work_specification_repo = DjangoWorkSpecificationRepository()
        return self._work_specification_repo

    @property
    def work_variant_creation_repo(self):
        if self._work_variant_creation_repo is None:
            self._work_variant_creation_repo = (
                DjangoWorkVariantCreationRepository()
            )
        return self._work_variant_creation_repo

    @property
    def variant_generation_form_repo(self):
        if self._variant_generation_form_repo is None:
            self._variant_generation_form_repo = (
                DjangoVariantGenerationFormRepository()
            )
        return self._variant_generation_form_repo

    @property
    def work_variant_composition_repo(self):
        if self._work_variant_composition_repo is None:
            self._work_variant_composition_repo = (
                DjangoWorkVariantCompositionRepository()
            )
        return self._work_variant_composition_repo

    @property
    def work_spec_sync_repo(self):
        if self._work_spec_sync_repo is None:
            self._work_spec_sync_repo = DjangoWorkSpecSyncRepository()
        return self._work_spec_sync_repo

    @property
    def work_read_repo(self):
        if self._work_read_repo is None:
            self._work_read_repo = DjangoWorkReadRepository()
        return self._work_read_repo

    @property
    def variant_read_repo(self):
        if self._variant_read_repo is None:
            self._variant_read_repo = DjangoVariantReadRepository()
        return self._variant_read_repo

    @property
    def variant_lifecycle_query_repo(self):
        if self._variant_lifecycle_query_repo is None:
            self._variant_lifecycle_query_repo = (
                DjangoVariantLifecycleQueryRepository()
            )
        return self._variant_lifecycle_query_repo

    @property
    def variant_lifecycle_command_repo(self):
        if self._variant_lifecycle_command_repo is None:
            self._variant_lifecycle_command_repo = (
                DjangoVariantLifecycleCommandRepository()
            )
        return self._variant_lifecycle_command_repo

    @property
    def orphan_variant_catalog_repo(self):
        if self._orphan_variant_catalog_repo is None:
            self._orphan_variant_catalog_repo = (
                DjangoOrphanVariantCatalogRepository()
            )
        return self._orphan_variant_catalog_repo

    @property
    def orphan_variant_attachment_repo(self):
        if self._orphan_variant_attachment_repo is None:
            self._orphan_variant_attachment_repo = (
                DjangoOrphanVariantAttachmentRepository()
            )
        return self._orphan_variant_attachment_repo

    @property
    def work_form_adapter(self):
        if self._work_form_adapter is None:
            self._work_form_adapter = WorkFormAdapter()
        return self._work_form_adapter

    def work_service(self):
        return WorkService()

    def prepare_delete_variant_submission_use_case(self):
        return PrepareDeleteVariantSubmissionUseCase()

    def prepare_bulk_delete_variants_submission_use_case(self):
        return PrepareBulkDeleteVariantsSubmissionUseCase()

    def prepare_create_work_from_orphans_submission_use_case(self):
        return PrepareCreateWorkFromOrphansSubmissionUseCase()

    def get_work_detail_use_case(self):
        return GetWorkDetailUseCase(
            work_read_repo=self.work_read_repo,
            work_service=self.work_service(),
            presentation_profile_repo=self.presentation_profile_catalog_repo,
        )

    def get_work_list_use_case(self):
        return GetWorkListUseCase(
            work_read_repo=self.work_read_repo,
        )

    def get_work_form_data_use_case(self):
        return GetWorkFormDataUseCase(
            work_read_repo=self.work_read_repo,
        )

    def get_variant_detail_use_case(self):
        return GetVariantDetailUseCase(
            variant_repo=self.variant_read_repo,
        )

    def get_variant_generation_form_use_case(self):
        return GetVariantGenerationFormUseCase(
            work_repo=self.variant_generation_form_repo,
        )

    def get_variant_list_use_case(self):
        return GetVariantListUseCase(
            variant_repo=self.variant_read_repo,
        )

    def get_orphan_variant_list_use_case(self):
        return GetOrphanVariantListUseCase(
            orphan_variant_repo=self.orphan_variant_catalog_repo,
        )

    def sync_work_analog_groups_use_case(self):
        return SyncWorkAnalogGroupsUseCase(
            work_repo=self.work_spec_sync_repo,
            transaction_manager=self.transaction_manager,
        )

    def compose_work_variants_use_case(self):
        return ComposeWorkVariantsUseCase(
            work_repo=self.work_variant_composition_repo,
            transaction_manager=self.transaction_manager,
        )

    def create_work_from_orphans_use_case(self):
        return CreateWorkFromOrphansUseCase(
            orphan_variant_repo=self.orphan_variant_attachment_repo,
        )

    def create_work_from_groups_use_case(self):
        return CreateWorkFromGroupsUseCase(
            task_group_repo=self.work_task_group_repo,
            create_work_with_specification_use_case=(
                self.create_work_with_specification_use_case()
            ),
            compose_work_variants_use_case=(
                self.compose_work_variants_use_case()
            ),
        )

    def prepare_create_work_from_groups_submission_use_case(self):
        return PrepareCreateWorkFromGroupsSubmissionUseCase()

    def create_work_from_tasks_use_case(self):
        return CreateWorkFromTasksUseCase(
            task_repo=self.task_selection_repo,
            work_repo=self.work_variant_creation_repo,
        )

    def create_work_with_specification_use_case(self):
        return CreateWorkWithSpecificationUseCase(
            work_repo=self.work_specification_repo,
        )

    def update_work_with_specification_use_case(self):
        return UpdateWorkWithSpecificationUseCase(
            work_repo=self.work_specification_repo,
        )

    def get_variant_delete_info_use_case(self):
        return GetVariantDeleteInfoUseCase(
            variant_repo=self.variant_lifecycle_query_repo,
        )

    def delete_variant_use_case(self):
        return DeleteVariantUseCase(
            variant_query_repo=self.variant_lifecycle_query_repo,
            variant_command_repo=self.variant_lifecycle_command_repo,
        )

    def bulk_delete_variants_use_case(self):
        return BulkDeleteVariantsUseCase(
            variant_query_repo=self.variant_lifecycle_query_repo,
            variant_command_repo=self.variant_lifecycle_command_repo,
        )
