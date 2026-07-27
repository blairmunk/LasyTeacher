"""Work screen read repository interface."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from core_logic.entities.work import (
    WorkDetailContentBlock,
    WorkDetailSpecGroup,
    WorkDetailSpecPreviewItem,
    WorkDetailVariant,
    WorkDetailWork,
    WorkListItem,
)


class IWorkReadRepository(ABC):
    @abstractmethod
    def get_list_works(self, filters=None) -> List[WorkListItem]:
        """Return works for the work list page."""

    @abstractmethod
    def get_work_form_analog_group_options(self) -> Any:
        """Return analog group options for the work form page."""

    @abstractmethod
    def get_work_detail(self, work_id: str) -> Optional[WorkDetailWork]:
        """Return one work detail read model, or None."""

    @abstractmethod
    def get_detail_variants(self, work_id: str) -> List[WorkDetailVariant]:
        """Return variant read models for the work detail page."""

    @abstractmethod
    def get_detail_analog_groups(
        self,
        work_id: str,
    ) -> List[WorkDetailSpecGroup]:
        """Return work specification read models for the work detail page."""

    @abstractmethod
    def get_detail_content_blocks(
        self,
        work_id: str,
    ) -> List[WorkDetailContentBlock]:
        """Return persistent non-task content in pedagogical order."""

    @abstractmethod
    def get_spec_preview(
        self,
        work_id: str,
    ) -> List[WorkDetailSpecPreviewItem]:
        """Return points specification preview rows for the work detail page."""
