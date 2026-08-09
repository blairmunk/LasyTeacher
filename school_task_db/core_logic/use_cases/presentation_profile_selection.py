"""Explicit document presentation profile selection."""

from core_logic.entities.document import DocumentPresentationProfile
from core_logic.interfaces.presentation_profile_repo import (
    IPresentationProfileRepository,
)


def resolve_document_presentation_profile(
    document_type: str,
    request_presentation_profile: DocumentPresentationProfile | None = None,
    request_presentation_profile_id: str = '',
    presentation_profile_repo: IPresentationProfileRepository | None = None,
) -> DocumentPresentationProfile | None:
    if request_presentation_profile is not None:
        return (
            request_presentation_profile
            if request_presentation_profile.document_type == document_type
            else None
        )
    if presentation_profile_repo is None:
        return None
    if request_presentation_profile_id:
        profile = presentation_profile_repo.get_presentation_profile(
            presentation_profile_id=request_presentation_profile_id,
            document_type=document_type,
        )
        return (
            profile
            if profile is not None and profile.document_type == document_type
            else None
        )
    return None
