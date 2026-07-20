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

    def test_builds_document_from_existing_paths(self):
        with TemporaryDirectory() as output_dir:
            file_path = Path(output_dir) / 'work.html'
            file_path.write_bytes(b'<html>work</html>')
            missing_path = Path(output_dir) / 'missing.html'
            store = RenderedDocumentFileStore()

            document = store.document_from_paths(
                file_type='html',
                file_paths=[file_path, missing_path],
            )

            self.assertEqual(document.file_type, 'html')
            self.assertEqual(len(document.files), 1)
            self.assertEqual(document.files[0].filename, 'work.html')
            self.assertGreater(document.files[0].size_kb, 0)

    def test_writes_text_document(self):
        with TemporaryDirectory() as output_dir:
            store = RenderedDocumentFileStore(
                output_dirs={'html': output_dir},
            )

            document = store.write_text_document(
                file_type='html',
                filename='work.html',
                content='<html>work</html>',
            )

            file_path = Path(output_dir) / 'work.html'
            self.assertEqual(
                file_path.read_text(encoding='utf-8'),
                '<html>work</html>',
            )
            self.assertEqual(document.file_type, 'html')
            self.assertEqual(len(document.files), 1)
            self.assertEqual(document.files[0].filename, 'work.html')

    def test_write_text_document_rejects_unknown_file_type(self):
        store = RenderedDocumentFileStore(output_dirs={'html': 'unused'})

        with self.assertRaises(ValueError):
            store.write_text_document(
                file_type='docx',
                filename='work.docx',
                content='work',
            )
