from abc import ABC, abstractmethod

from opengaterag.api.domain.document.entities import Document
from opengaterag.api.domain.document.errors import DocumentNotFoundError


class DocumentRepository(ABC):
    @abstractmethod
    async def get_document(self, document_id: int) -> Document | DocumentNotFoundError:
        pass

    @abstractmethod
    async def get_documents(self, collection_id: int, offset: int, limit: int) -> tuple[list[Document], int]:
        """Return one page of the documents in the collection, and the total number of documents in it."""
        pass
