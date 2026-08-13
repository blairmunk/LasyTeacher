"""Prepare data for the presentation profile editor."""

from dataclasses import dataclass

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.interfaces.presentation_profile_catalog_repo import (
    IPresentationProfileCatalogRepository,
)
from core_logic.value_objects.document_type_catalog import (
    DocumentTypeCatalogItem,
    get_document_type_catalog,
)


@dataclass(frozen=True)
class GetPresentationProfileEditorDataRequest:
    document_type: str = ''
    renderable_only: bool = False


@dataclass(frozen=True)
class PresentationProfileEditorData:
    document_types: tuple[DocumentTypeCatalogItem, ...]
    presentation_profiles: tuple[DocumentPresentationProfile, ...]


class GetPresentationProfileEditorDataUseCase:
    """Prepare presentation profiles and supported document types."""

    def __init__(
        self,
        presentation_profile_repo: (
            IPresentationProfileCatalogRepository | None
        ) = None,
    ):
        self.presentation_profile_repo = presentation_profile_repo

    def execute(
        self,
        request: GetPresentationProfileEditorDataRequest | None = None,
    ) -> PresentationProfileEditorData:
        request = request or GetPresentationProfileEditorDataRequest()
        return PresentationProfileEditorData(
            document_types=get_document_type_catalog(
                renderable_only=request.renderable_only,
            ),
            presentation_profiles=self._presentation_profiles(
                request.document_type,
            ),
        )

    def _presentation_profiles(
        self,
        document_type: str,
    ) -> tuple[DocumentPresentationProfile, ...]:
        if self.presentation_profile_repo is None:
            return ()
        return tuple(
            self.presentation_profile_repo.list_presentation_profiles(
                document_type=document_type,
            ),
        )
