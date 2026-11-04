from abc import ABC, abstractmethod

from opengaterag.api.domain.document.entities import Chunk
from opengaterag.api.domain.search.errors import ChunkEmbeddingFailedError


class ChunkIndex(ABC):
    @abstractmethod
    async def add_chunks(self, chunks: list[Chunk]) -> None | ChunkEmbeddingFailedError:
        pass

    @abstractmethod
    async def delete_document_chunks(self, document_id: int) -> None:
        pass

    @abstractmethod
    async def delete_collection_chunks(self, collection_id: int) -> None:
        pass
