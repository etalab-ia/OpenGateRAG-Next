from abc import ABC, abstractmethod

from opengaterag.api.domain.document.errors import UnsupportedFileTypeError


class DocumentParser(ABC):
    @abstractmethod
    async def parse(self, file_name: str, content_type: str | None, content: bytes) -> str | UnsupportedFileTypeError:
        """Return the text of the file."""
        pass
