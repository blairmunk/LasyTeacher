"""Filesystem access for rendered document files."""

import mimetypes
from pathlib import Path

from core_logic.entities.document_rendering import (
    GENERATED_FILE_STATUS_NOT_FOUND,
    GENERATED_FILE_STATUS_READ_ERROR,
    GENERATED_FILE_STATUS_READY,
    GENERATED_FILE_STATUS_UNSUPPORTED_TYPE,
    GeneratedDocument,
    GeneratedDocumentFile,
    GeneratedFile,
    GeneratedFileResult,
)


class RenderedDocumentFileStore:
    default_output_dirs = {
        'latex': 'web_latex_output',
        'html': 'web_html_output',
        'pdf': 'web_pdf_output',
    }

    def __init__(self, output_dirs=None):
        self.output_dirs = output_dirs or self.default_output_dirs

    def get_file(self, file_type: str, filename: str) -> GeneratedFileResult:
        output_dir = self.output_dirs.get(file_type)
        if not output_dir:
            return GeneratedFileResult(status=GENERATED_FILE_STATUS_UNSUPPORTED_TYPE)

        file_path = Path(output_dir) / filename
        if not file_path.exists():
            return GeneratedFileResult(status=GENERATED_FILE_STATUS_NOT_FOUND)

        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = 'application/octet-stream'

        try:
            return GeneratedFileResult(
                status=GENERATED_FILE_STATUS_READY,
                file=GeneratedFile(
                    filename=filename,
                    content=file_path.read_bytes(),
                    content_type=content_type,
                ),
            )
        except OSError:
            return GeneratedFileResult(status=GENERATED_FILE_STATUS_READ_ERROR)

    def document_from_paths(self, file_type: str, file_paths):
        files = []
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists():
                files.append(
                    GeneratedDocumentFile(
                        filename=path.name,
                        size_kb=path.stat().st_size / 1024,
                    )
                )

        return GeneratedDocument(file_type=file_type, files=files)

    def write_text_document(
        self,
        file_type: str,
        filename: str,
        content: str,
    ) -> GeneratedDocument:
        output_dir = self.output_dirs.get(file_type)
        if not output_dir:
            raise ValueError(f'unsupported file type: {file_type}')

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        file_path = output_path / filename
        file_path.write_text(content, encoding='utf-8')

        return self.document_from_paths(file_type, [file_path])
