"""Wire Django-backed section payload builders into document registries."""

from core_logic.services.document_builder import (
    DocumentSectionPayloadBuilderRegistry,
)
from core_logic.value_objects.document_recipes import (
    ANSWER_KEY_SECTION,
    ANSWERS_SECTION,
    BLANK_CELLS_SECTION,
    COMMON_HEADER_SECTION,
    FULL_SOLUTIONS_SECTION,
    HEADER_SECTION,
    ORIGINAL_MISTAKES_SECTION,
    REMEDIAL_SHEET_DOCUMENT_TYPE,
    SHORT_SOLUTIONS_SECTION,
    TASK_LIST_SECTION,
    THEORY_SECTION,
    TRAINING_TASKS_SECTION,
    WORK_DOCUMENT_TYPE,
)
from core_logic.entities.document import (
    REMEDIAL_WORK_SOURCE_TYPE,
    REMEDIAL_VARIANT_SOURCE_TYPE,
    WORK_SOURCE_TYPE,
)
from infrastructure.services.blank_cells_payload import (
    build_blank_cells_payload,
)
from infrastructure.services.django_remedial_document_payloads import (
    DjangoRemedialHeaderPayloadBuilder,
    DjangoRemedialOriginalMistakesPayloadBuilder,
    DjangoRemedialTrainingTasksPayloadBuilder,
    RemedialSheetDataProvider,
)
from infrastructure.services.django_work_document_payloads import (
    DjangoWorkHeaderPayloadBuilder,
    DjangoWorkTaskListPayloadBuilder,
    DjangoWorkTheoryPayloadBuilder,
)


class BlankCellsPayloadBuilder:
    def build_payload(self, request):
        return build_blank_cells_payload(request.section.options)


def build_work_section_payload_builder_registry(
    get_work_source=None,
    task_payload_formatter=None,
) -> DocumentSectionPayloadBuilderRegistry:
    registry = DocumentSectionPayloadBuilderRegistry()
    task_list_builder = DjangoWorkTaskListPayloadBuilder(
        get_work_source=get_work_source,
        task_payload_formatter=task_payload_formatter,
    )
    registry.register(
        COMMON_HEADER_SECTION,
        DjangoWorkHeaderPayloadBuilder(get_work_source=get_work_source),
        document_type=WORK_DOCUMENT_TYPE,
        source_type=WORK_SOURCE_TYPE,
    )
    registry.register(
        HEADER_SECTION,
        DjangoWorkHeaderPayloadBuilder(get_work_source=get_work_source),
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
        THEORY_SECTION,
        DjangoWorkTheoryPayloadBuilder(
            get_work_source=get_work_source,
            task_payload_formatter=task_payload_formatter,
        ),
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
    header_builder = DjangoRemedialHeaderPayloadBuilder(sheet_data_provider)
    original_mistakes_builder = DjangoRemedialOriginalMistakesPayloadBuilder(
        sheet_data_provider,
        task_payload_formatter=task_payload_formatter,
    )
    training_tasks_builder = DjangoRemedialTrainingTasksPayloadBuilder(
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
