"""Framework-independent contract for files crossing into application commands."""

from typing import Iterator, Protocol


class UploadedFile(Protocol):
    """Readable file accepted by persistence adapters without a Django import."""

    name: str

    def read(self, size: int = -1) -> bytes:
        """Read bytes from the current stream position."""

    def chunks(self, chunk_size: int | None = None) -> Iterator[bytes]:
        """Yield bounded chunks when the backing upload supports streaming."""
