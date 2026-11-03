import asyncio
from enum import StrEnum
from pathlib import Path

from html_to_markdown import convert
import pymupdf
import pymupdf4llm

from opengaterag.api.domain.document import DocumentParser
from opengaterag.api.domain.document.errors import UnsupportedFileTypeError


class FileType(StrEnum):
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"


FILE_TYPES_BY_EXTENSION = {
    ".pdf": FileType.PDF,
    ".html": FileType.HTML,
    ".htm": FileType.HTML,
    ".md": FileType.MARKDOWN,
    ".markdown": FileType.MARKDOWN,
    ".txt": FileType.TEXT,
}
FILE_TYPES_BY_CONTENT_TYPE = {
    "application/pdf": FileType.PDF,
    "text/html": FileType.HTML,
    "text/markdown": FileType.MARKDOWN,
    "text/plain": FileType.TEXT,
}


class MarkdownDocumentParser(DocumentParser):
    """Convert PDF and HTML files to Markdown with PyMuPDF and html-to-markdown, and read Markdown and plain text as is."""

    async def parse(self, file_name: str, content_type: str | None, content: bytes) -> str | UnsupportedFileTypeError:
        file_type = FILE_TYPES_BY_EXTENSION.get(Path(file_name).suffix.lower()) or FILE_TYPES_BY_CONTENT_TYPE.get(content_type)

        match file_type:
            case FileType.PDF:
                # PDF conversion is CPU-bound: run it in a thread so that it does not block the event loop.
                return await asyncio.to_thread(self._convert_pdf, content)
            case FileType.HTML:
                return convert(self._decode(content)).strip()
            case FileType.MARKDOWN | FileType.TEXT:
                return self._decode(content).strip()
            case None:
                return UnsupportedFileTypeError()

    @staticmethod
    def _convert_pdf(content: bytes) -> str:
        with pymupdf.open(stream=content, filetype="pdf") as pdf:
            return pymupdf4llm.to_markdown(pdf).strip()

    @staticmethod
    def _decode(content: bytes) -> str:
        try:
            return content.decode("utf-8")
        except UnicodeDecodeError:
            return content.decode("latin-1")
