import httpx

from opengaterag.api.domain.document.entities import Chunk
from opengaterag.api.domain.search import ChunkIndex
from opengaterag.api.domain.search.errors import ChunkEmbeddingFailedError
from opengaterag.api.infrastructure.meilisearch._meilisearchtask import raise_unsuccessful_task, wait_for_task

EMBEDDING_ERROR_CODE = "vector_embedding_error"


class MeilisearchChunkIndex(ChunkIndex):
    def __init__(self, meilisearch_client: httpx.AsyncClient, index_name: str, task_timeout: int):
        self.meilisearch_client = meilisearch_client
        self.index_name = index_name
        self.task_timeout = task_timeout

    async def add_chunks(self, chunks: list[Chunk]) -> None | ChunkEmbeddingFailedError:
        records = [{"id": f"{chunk.document_id}-{chunk.position}", **chunk.model_dump()} for chunk in chunks]
        response = await self.meilisearch_client.post(f"/indexes/{self.index_name}/documents", json=records)
        response.raise_for_status()
        task = await wait_for_task(self.meilisearch_client, task_uid=response.json()["taskUid"], task_timeout=self.task_timeout)

        if (task.get("error") or {}).get("code") == EMBEDDING_ERROR_CODE:
            return ChunkEmbeddingFailedError()

        raise_unsuccessful_task(task)

        return None

    async def delete_document_chunks(self, document_id: int) -> None:
        response = await self.meilisearch_client.post(f"/indexes/{self.index_name}/documents/delete", json={"filter": f"document_id = {document_id}"})
        response.raise_for_status()
        task = await wait_for_task(self.meilisearch_client, task_uid=response.json()["taskUid"], task_timeout=self.task_timeout)

        raise_unsuccessful_task(task)
