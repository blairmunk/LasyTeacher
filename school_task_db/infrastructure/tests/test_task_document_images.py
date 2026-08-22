from pathlib import Path
from types import SimpleNamespace
from tempfile import TemporaryDirectory

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.test import SimpleTestCase

from core_logic.value_objects.document_render_options import RenderTarget
from infrastructure.services.task_document_images import (
    TaskDocumentImagePayloadFormatter,
)


class TaskDocumentImagePayloadFormatterTests(SimpleTestCase):
    def test_embeds_existing_image_in_standalone_html_payload(self):
        with TemporaryDirectory() as media_root:
            storage = FileSystemStorage(location=media_root)
            storage.save('task_images/diagram.png', ContentFile(b'PNG'))
            request = self._request('html')

            formatted = TaskDocumentImagePayloadFormatter(
                storage=storage,
            ).format_task_payload(
                self._payload(position='right_40'),
                request=request,
            )

        image = formatted['images'][0]
        self.assertEqual(image['render_source'], 'data:image/png;base64,UE5H')
        self.assertEqual(image['placement'], 'right')
        self.assertEqual(image['width_percent'], 40)
        self.assertEqual(formatted['right_images'], (image,))
        self.assertEqual(formatted['bottom_images'], ())
        self.assertIn(
            ('html', 'task_images/diagram.png'),
            request.build_context['task_image_render_sources'],
        )

    def test_resolves_existing_image_to_latex_include_argument(self):
        with TemporaryDirectory() as media_root:
            storage = FileSystemStorage(location=media_root)
            stored_name = storage.save(
                'task_images/diagram with spaces.png',
                ContentFile(b'PNG'),
            )
            payload = self._payload(
                position='bottom_100',
                file_name=stored_name,
            )

            formatted = TaskDocumentImagePayloadFormatter(
                storage=storage,
            ).format_task_payload(
                payload,
                request=self._request('latex'),
            )

        image = formatted['images'][0]
        expected_path = Path(media_root, stored_name).resolve()
        self.assertEqual(
            image['render_source'],
            r'{\detokenize{' + str(expected_path) + '}}',
        )
        self.assertEqual(image['placement'], 'bottom')
        self.assertEqual(image['width_fraction'], '1')

    def test_omits_missing_file_without_failing_document_payload(self):
        with TemporaryDirectory() as media_root:
            formatter = TaskDocumentImagePayloadFormatter(
                storage=FileSystemStorage(location=media_root),
            )

            formatted = formatter.format_task_payload(
                self._payload(),
                request=self._request('pdf'),
            )

        self.assertEqual(formatted['images'], ())
        self.assertEqual(formatted['right_images'], ())
        self.assertEqual(formatted['bottom_images'], ())

    def test_unknown_position_uses_bottom_seventy_percent_layout(self):
        with TemporaryDirectory() as media_root:
            storage = FileSystemStorage(location=media_root)
            storage.save('task_images/diagram.png', ContentFile(b'PNG'))

            formatted = TaskDocumentImagePayloadFormatter(
                storage=storage,
            ).format_task_payload(
                self._payload(position='unknown'),
                request=self._request('html'),
            )

        image = formatted['images'][0]
        self.assertEqual(image['placement'], 'bottom')
        self.assertEqual(image['width_percent'], 70)
        self.assertEqual(formatted['bottom_images'], (image,))

    @staticmethod
    def _payload(position='bottom_70', file_name='task_images/diagram.png'):
        return {
            'text': 'Задание',
            'images': ({
                'image_id': 'image-1',
                'file_name': file_name,
                'position': position,
                'caption': 'Схема',
                'order': 1,
            },),
        }

    @staticmethod
    def _request(renderer_type):
        return SimpleNamespace(
            render_target=RenderTarget(renderer_type=renderer_type),
            build_context={},
        )
