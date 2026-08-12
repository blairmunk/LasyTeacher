"""Prepare data for the presentation profile form."""

from dataclasses import dataclass
from typing import Tuple

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.interfaces.presentation_profile_catalog_repo import (
    IPresentationProfileCatalogRepository,
)
from core_logic.value_objects.document_type_catalog import (
    DocumentTypeCatalogItem,
    get_document_type_catalog,
)


@dataclass(frozen=True)
class GetPresentationProfileFormDataRequest:
    presentation_profile_id: str = ''
    renderable_only: bool = True


@dataclass(frozen=True)
class PresentationProfileFormData:
    document_types: Tuple[DocumentTypeCatalogItem, ...]
    presentation_profile: DocumentPresentationProfile | None = None


class GetPresentationProfileFormDataUseCase:
    """Prepare a presentation profile and supported document types."""

    def __init__(
        self,
        presentation_profile_repo: (
            IPresentationProfileCatalogRepository | None
        ) = None,
    ):
        self.presentation_profile_repo = presentation_profile_repo

    def execute(
        self,
        request: GetPresentationProfileFormDataRequest | None = None,
    ) -> PresentationProfileFormData:
        request = request or GetPresentationProfileFormDataRequest()
        return PresentationProfileFormData(
            document_types=get_document_type_catalog(
                renderable_only=request.renderable_only,
            ),
            presentation_profile=self._presentation_profile(
                request.presentation_profile_id,
            ),
        )

    def _presentation_profile(
        self,
        presentation_profile_id: str,
    ) -> DocumentPresentationProfile | None:
        if (
            not presentation_profile_id
            or self.presentation_profile_repo is None
        ):
            return None
        return self.presentation_profile_repo.get_presentation_profile(
            presentation_profile_id=presentation_profile_id,
        )
