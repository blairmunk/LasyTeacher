"""Infrastructure helpers for Django core forms and query params."""

from core_logic.entities.task import TaskExportFilters
from core_logic.entities.task_import import (
    TaskImportExecutionSubmissionRequest,
    TaskImportFileRequest,
)
from core_logic.use_cases.export_tasks import ExportTasksRequest
from core_logic.use_cases.get_global_search import GlobalSearchRequest


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
