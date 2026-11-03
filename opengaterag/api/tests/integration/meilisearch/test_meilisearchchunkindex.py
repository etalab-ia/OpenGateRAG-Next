from opengaterag.api.domain.document.entities import Chunk
from opengaterag.api.infrastructure.meilisearch import MeilisearchChunkIndex
from opengaterag.api.tests.integration.meilisearch.conftest import TASK_TIMEOUT


def _chunk(document_id: int, position: int) -> Chunk:
    return Chunk(document_id=document_id, collection_id=7, position=position, content=f"Part {position}.", metadata={"source_title": "Report"})


async def _get_chunk_ids(meilisearch_client, index_name: str) -> list[str]:
    response = await meilisearch_client.get(f"/indexes/{index_name}/documents", params={"fields": "id"})
    response.raise_for_status()

    return sorted(record["id"] for record in response.json()["results"])


class TestAddChunks:
    async def test_should_index_chunks_under_document_id_and_position(self, meilisearch_client, index_name):
        # Arrange
        chunk_index = MeilisearchChunkIndex(meilisearch_client=meilisearch_client, index_name=index_name, task_timeout=TASK_TIMEOUT)

        # Act
        result = await chunk_index.add_chunks(chunks=[_chunk(document_id=42, position=0), _chunk(document_id=42, position=1)])

        # Assert
        assert result is None
        response = await meilisearch_client.get(f"/indexes/{index_name}/documents/42-1")
        assert response.json() == {
            "id": "42-1",
            "document_id": 42,
            "collection_id": 7,
            "position": 1,
            "content": "Part 1.",
            "metadata": {"source_title": "Report"},
        }


class TestDeleteDocumentChunks:
    async def test_should_delete_chunks_of_document_only(self, meilisearch_client, index_name):
        # Arrange
        chunk_index = MeilisearchChunkIndex(meilisearch_client=meilisearch_client, index_name=index_name, task_timeout=TASK_TIMEOUT)
        await chunk_index.add_chunks(chunks=[_chunk(document_id=42, position=0), _chunk(document_id=42, position=1), _chunk(document_id=43, position=0)])  # fmt: off

        # Act
        await chunk_index.delete_document_chunks(document_id=42)

        # Assert
        assert await _get_chunk_ids(meilisearch_client, index_name) == ["43-0"]
