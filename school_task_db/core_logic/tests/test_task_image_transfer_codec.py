from django.test import SimpleTestCase

from core_logic.services.task_image_transfer_codec import (
    TaskImageTransferCodec,
)


class TaskImageTransferCodecTests(SimpleTestCase):
    def setUp(self):
        self.codec = TaskImageTransferCodec()

    def test_round_trip_preserves_binary_content(self):
        content = b'\x89PNG\r\n\x1a\n\x00binary-image'

        encoded = self.codec.encode(content)

        self.assertEqual(self.codec.decode(encoded), content)

    def test_decode_accepts_data_uri_payload(self):
        self.assertEqual(
            self.codec.decode('data:image/png;base64,aW1hZ2U='),
            b'image',
        )

    def test_rejects_empty_non_string_and_malformed_payloads(self):
        for value in (None, b'aW1hZ2U=', '', 'data:image/png;base64,', 'bad!'):
            with self.subTest(value=value):
                self.assertFalse(self.codec.is_valid(value))
                with self.assertRaises(ValueError):
                    self.codec.decode(value)

    def test_encode_requires_bytes(self):
        with self.assertRaises(TypeError):
            self.codec.encode('image')
