"""Infrastructure helpers for Django core forms and query params."""

from core_logic.entities.task import TaskExportFilters
from core_logic.entities.task_import import (
    TaskImportExecutionSubmissionRequest,
    TaskImportFileRequest,
    TaskImportPreviewRequest,
)
from core_logic.use_cases.export_tasks import ExportTasksRequest
from core_logic.use_cases.get_global_search import GlobalSearchRequest
from core_logic.use_cases.validate_task_import_json import (
    ValidateTaskImportJsonRequest,
)


class CoreFormAdapter:
    def global_search_request_from_query(self, query):
        return GlobalSearchRequest(raw_query=query.get('q', ''))

    def task_import_file_request_from_upload(self, uploaded_file):
        return TaskImportFileRequest(
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            content=uploaded_file.read(),
        )

    def task_import_execution_submission_from_upload(self, uploaded_file, post_data):
        return TaskImportExecutionSubmissionRequest(
            filename=uploaded_file.name,
            file_size=uploaded_file.size,
            content=uploaded_file.read(),
            form_data=self._post_lists(post_data),
        )

    def validate_task_import_json_request_from_data(self, data):
        return ValidateTaskImportJsonRequest(data=data)

    def task_import_preview_request_from_data(self, data):
        return TaskImportPreviewRequest(data=data)

    def export_tasks_request_from_query(self, query, export_date):
        return ExportTasksRequest(
            filters=TaskExportFilters(
                topic_id=query.get('topic', ''),
                subject=query.get('subject', ''),
                grade=query.get('grade', ''),
            ),
            export_date=export_date,
        )

    def _post_lists(self, post_data):
        return {
            key: post_data.getlist(key)
            for key in post_data
        }
