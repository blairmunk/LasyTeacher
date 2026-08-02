"""Wire Django-backed section payload builders into document registries."""

from core_logic.services.document_builder import (
    DocumentSectionPayloadBuilderRegistry,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    COMMON_HEADER_SECTION,
    EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
    EVENT_REPORT_CONCLUSIONS_SECTION,
    EVENT_REPORT_SUMMARY_SECTION,
    EVENT_REPORT_SPECIFICATION_SECTION,
    EVENT_REPORT_TASK_ANALYSIS_SECTION,
    EVENT_REPORT_TEACHER_NOTES_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    STUDENT_DIGEST_DETAILS_SECTION,
    STUDENT_DIGEST_DOCUMENT_TYPE,
    STUDENT_DIGEST_FOCUS_SECTION,
    STUDENT_DIGEST_RETAKES_SECTION,
    STUDENT_DIGEST_SUMMARY_SECTION,
    TASK_LIST_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.entities.document import (
    EVENT_REPORT_SOURCE_TYPE,
    REMEDIAL_WORK_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    STUDENT_DIGEST_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from infrastructure.services.blank_cells_payload import (
    build_blank_cells_payload,
)
from infrastructure.services.remedial_document_payloads import (
    RemedialHeaderPayloadBuilder,
    RemedialOriginalMistakesPayloadBuilder,
    RemedialTrainingTasksPayloadBuilder,
    RemedialSheetDataProvider,
)
from infrastructure.services.django_work_document_payloads import (
    DjangoWorkHeaderPayloadBuilder,
    DjangoWorkTaskListPayloadBuilder,
    WorkDocumentSourceProvider,
)
from infrastructure.services.django_report_document_payloads import (
    EventReportDocumentDataProvider,
    EventReportSectionPayloadBuilder,
    StudentDigestDocumentDataProvider,
    StudentDigestSectionPayloadBuilder,
)


class BlankCellsPayloadBuilder:
    def build_payload(self, request):
        return build_blank_cells_payload(request.section.options)


def build_work_section_payload_builder_registry(
    get_work_source=None,
    task_payload_formatter=None,
) -> DocumentSectionPayloadBuilderRegistry:
    registry = DocumentSectionPayloadBuilderRegistry()
    work_source_provider = WorkDocumentSourceProvider(
        get_work_source=get_work_source,
    )
    task_list_builder = DjangoWorkTaskListPayloadBuilder(
        task_payload_formatter=task_payload_formatter,
        work_source_provider=work_source_provider,
    )
    header_builder = DjangoWorkHeaderPayloadBuilder(
        work_source_provider=work_source_provider,
    )
    registry.register(
        COMMON_HEADER_SECTION,
        header_builder,
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        HEADER_SECTION,
        header_builder,
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        TASK_LIST_SECTION,
        task_list_builder,
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        BLANK_CELLS_SECTION,
        BlankCellsPayloadBuilder(),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    for section_type in (
        ANSWERS_SECTION,
        ANSWER_KEY_SECTION,
        SHORT_SOLUTIONS_SECTION,
        FULL_SOLUTIONS_SECTION,
    ):
        registry.register(
            section_type,
            task_list_builder,
            document_type=WORK_DOCUMENT_TYPE,
            source_type=WORK_SOURCE_TYPE,
        )
    return registry


def build_remedial_sheet_section_payload_builder_registry(
    get_remedial_sheet_data,
    task_payload_formatter=None,
) -> DocumentSectionPayloadBuilderRegistry:
    sheet_data_provider = RemedialSheetDataProvider(
        get_remedial_sheet_data=get_remedial_sheet_data,
    )
    registry = DocumentSectionPayloadBuilderRegistry()
    header_builder = RemedialHeaderPayloadBuilder(sheet_data_provider)
    original_mistakes_builder = RemedialOriginalMistakesPayloadBuilder(
        sheet_data_provider,
        task_payload_formatter=task_payload_formatter,
    )
    training_tasks_builder = RemedialTrainingTasksPayloadBuilder(
        sheet_data_provider,
        task_payload_formatter=task_payload_formatter,
    )
    blank_cells_builder = BlankCellsPayloadBuilder()
    for source_type in (REMEDIAL_VARIANT_SOURCE_TYPE, REMEDIAL_WORK_SOURCE_TYPE):
        registry.register(
            HEADER_SECTION,
            header_builder,
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            source_type=source_type,
        )
        registry.register(
            ORIGINAL_MISTAKES_SECTION,
            original_mistakes_builder,
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            source_type=source_type,
        )
        registry.register(
            BLANK_CELLS_SECTION,
            blank_cells_builder,
            document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
            source_type=source_type,
        )
    for section_type in (
        TRAINING_TASKS_SECTION,
        ANSWERS_SECTION,
        SHORT_SOLUTIONS_SECTION,
        FULL_SOLUTIONS_SECTION,
    ):
        for source_type in (
            REMEDIAL_VARIANT_SOURCE_TYPE,
            REMEDIAL_WORK_SOURCE_TYPE,
        ):
            registry.register(
                section_type,
                training_tasks_builder,
                document_type=REMEDIAL_SHEET_DOCUMENT_TYPE,
                source_type=source_type,
            )
    return registry


def build_report_section_payload_builder_registry(
    get_event_report,
    get_student_digests,
) -> DocumentSectionPayloadBuilderRegistry:
    registry = DocumentSectionPayloadBuilderRegistry()
    event_builder = EventReportSectionPayloadBuilder(
        EventReportDocumentDataProvider(get_event_report),
    )
    for section_type in (
        HEADER_SECTION,
        EVENT_REPORT_SPECIFICATION_SECTION,
        EVENT_REPORT_SUMMARY_SECTION,
        EVENT_REPORT_TASK_ANALYSIS_SECTION,
        EVENT_REPORT_CONCLUSIONS_SECTION,
        EVENT_REPORT_TEACHER_NOTES_SECTION,
    ):
        registry.register(
            section_type,
            event_builder,
            document_type=EVENT_PERFORMANCE_REPORT_DOCUMENT_TYPE,
            source_type=EVENT_REPORT_SOURCE_TYPE,
        )

    digest_builder = StudentDigestSectionPayloadBuilder(
        StudentDigestDocumentDataProvider(get_student_digests),
    )
    for section_type in (
        HEADER_SECTION,
        STUDENT_DIGEST_SUMMARY_SECTION,
        STUDENT_DIGEST_RETAKES_SECTION,
        STUDENT_DIGEST_DETAILS_SECTION,
        STUDENT_DIGEST_FOCUS_SECTION,
    ):
        registry.register(
            section_type,
            digest_builder,
            document_type=STUDENT_DIGEST_DOCUMENT_TYPE,
            source_type=STUDENT_DIGEST_SOURCE_TYPE,
        )
    return registry
