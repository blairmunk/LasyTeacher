"""Content options for sectioned written-report documents."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventReportDocumentOptions:
    include_specification: bool = True
    include_summary: bool = True
    include_task_analysis: bool = True
    include_conclusions: bool = True
    include_content_element_text: bool = True
    include_teacher_notes: bool = False
