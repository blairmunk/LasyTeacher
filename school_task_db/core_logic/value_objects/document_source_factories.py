"""Factories for document source references."""

from core_logic.entities.document import (
    DocumentSourceRef,
    EVENT_REPORT_SOURCE_TYPE,
    REMEDIAL_WORK_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    STUDENT_DIGEST_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)


def build_work_document_source(
    work_id: str,
    work_name: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=WORK_SOURCE_TYPE,
        source_id=work_id,
        title=work_name,
    )


def build_remedial_sheet_document_source(
    variant_id: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=REMEDIAL_VARIANT_SOURCE_TYPE,
        source_id=variant_id,
        title='Работа над ошибками',
    )


def build_remedial_sheet_batch_document_source(
    work_id: str,
    work_name: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=REMEDIAL_WORK_SOURCE_TYPE,
        source_id=work_id,
        title=work_name,
    )


def build_event_report_document_source(
    event_id: str,
    event_name: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=EVENT_REPORT_SOURCE_TYPE,
        source_id=event_id,
        title=event_name,
    )


def build_student_digest_document_source(
    group_id: str,
    group_name: str,
) -> DocumentSourceRef:
    return DocumentSourceRef(
        source_type=STUDENT_DIGEST_SOURCE_TYPE,
        source_id=group_id,
        title=f'Дайджест оценок: {group_name}',
    )
