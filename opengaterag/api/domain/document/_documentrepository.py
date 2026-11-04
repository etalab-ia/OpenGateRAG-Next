from abc import ABC, abstractmethod

from opengaterag.api.domain.document.entities import Document, DocumentMetadata
from opengaterag.api.domain.document.errors import DocumentNotFoundError


class DocumentRepository(ABC):
    @abstractmethod
    async def create_document(self, collection_id: int, name: str, metadata: DocumentMetadata) -> Document:
        pass

    @abstractmethod
    async def get_document(self, document_id: int) -> Document | DocumentNotFoundError:
        pass

    @abstractmethod
    async def get_documents(self, collection_id: int, offset: int, limit: int) -> tuple[list[Document], int]:
        """Return one page of the documents in the collection, and the total number of documents in it."""
        pass

    @abstractmethod
    async def delete_document(self, document_id: int) -> None | DocumentNotFoundError:
        pass
