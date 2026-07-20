from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from core_logic.entities.document_rendering import (
    GENERATED_FILE_STATUS_NOT_FOUND,
    GENERATED_FILE_STATUS_READY,
    GENERATED_FILE_STATUS_UNSUPPORTED_TYPE,
)
from infrastructure.services.rendered_document_file_store import (
    RenderedDocumentFileStore,
)


class RenderedDocumentFileStoreTests(TestCase):
    def test_returns_rendered_file_contents(self):
        with TemporaryDirectory() as output_dir:
            file_path = Path(output_dir) / 'work.html'
            file_path.write_bytes(b'<html>work</html>')
            store = RenderedDocumentFileStore(
                output_dirs={'html': output_dir},
            )

            result = store.get_file(file_type='html', filename='work.html')

            self.assertEqual(result.status, GENERATED_FILE_STATUS_READY)
            self.assertEqual(result.file.filename, 'work.html')
            self.assertEqual(result.file.content, b'<html>work</html>')
            self.assertEqual(result.file.content_type, 'text/html')

    def test_returns_not_found_for_missing_file(self):
        with TemporaryDirectory() as output_dir:
            store = RenderedDocumentFileStore(
                output_dirs={'html': output_dir},
            )

            result = store.get_file(file_type='html', filename='missing.html')

            self.assertEqual(result.status, GENERATED_FILE_STATUS_NOT_FOUND)

    def test_returns_unsupported_for_unknown_file_type(self):
        store = RenderedDocumentFileStore(output_dirs={'html': 'unused'})

        result = store.get_file(file_type='docx', filename='work.docx')

        self.assertEqual(result.status, GENERATED_FILE_STATUS_UNSUPPORTED_TYPE)
