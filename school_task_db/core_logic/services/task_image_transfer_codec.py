"""Encoding for task-image binary data in portable transfer files."""

import base64
import binascii


class TaskImageTransferCodec:
    """Translate image bytes to and from the JSON-safe transfer format."""

    @staticmethod
    def encode(content: bytes) -> str:
        if not isinstance(content, bytes):
            raise TypeError('Image content must be bytes')
        return base64.b64encode(content).decode('ascii')

    @staticmethod
    def decode(value: str) -> bytes:
        if not isinstance(value, str) or not value:
            raise ValueError('Image transfer data must be a non-empty string')

        encoded = value.split(',', 1)[1] if ',' in value else value
        if not encoded:
            raise ValueError('Image transfer data is empty')
        try:
            return base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as error:
            raise ValueError('Invalid base64 image transfer data') from error

    @classmethod
    def is_valid(cls, value) -> bool:
        try:
            cls.decode(value)
        except (TypeError, ValueError):
            return False
        return True
