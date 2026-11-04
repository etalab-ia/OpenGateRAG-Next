from pathlib import Path

from opengaterag.api.domain.document import DocumentParser
from opengaterag.api.domain.document.errors import UnsupportedFileTypeError

SUPPORTED_EXTENSIONS = (".md", ".markdown", ".txt")
SUPPORTED_CONTENT_TYPES = ("text/markdown", "text/plain")


class MarkdownDocumentParser(DocumentParser):
    """Read Markdown and plain text files as is."""

    async def parse(self, file_name: str, content_type: str | None, content: bytes) -> str | UnsupportedFileTypeError:
        if Path(file_name).suffix.lower() not in SUPPORTED_EXTENSIONS and content_type not in SUPPORTED_CONTENT_TYPES:
            return UnsupportedFileTypeError()

        return content.decode("utf-8", errors="replace").strip()
