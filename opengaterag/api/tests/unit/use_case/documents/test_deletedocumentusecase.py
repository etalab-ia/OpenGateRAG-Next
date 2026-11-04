from datetime import UTC, datetime
from unittest.mock import create_autospec

import httpx
import pytest

from opengaterag.api.domain.collection import CollectionQuery
from opengaterag.api.domain.collection.entities import CollectionVisibility
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.domain.collection.views import CollectionView
from opengaterag.api.domain.document import DocumentRepository
from opengaterag.api.domain.document.entities import Document
from opengaterag.api.domain.document.errors import DocumentNotFoundError
from opengaterag.api.domain.search import ChunkIndex
from opengaterag.api.use_cases.documents import DeleteDocumentCommand, DeleteDocumentUseCase, DeleteDocumentUseCaseSuccess

OWNER_ID = 1
OTHER_USER_ID = 2
COLLECTION_ID = 7
DOCUMENT_ID = 42
NOW = datetime(2030, 1, 1, tzinfo=UTC)

DOCUMENT = Document(id=DOCUMENT_ID, collection_id=COLLECTION_ID, name="report.md", attributes={}, created=NOW)


def _collection_view(visibility: CollectionVisibility = CollectionVisibility.PRIVATE) -> CollectionView:
    return CollectionView(
        id=COLLECTION_ID,
        user_id=OWNER_ID,
        name="my-collection",
        description=None,
        visibility=visibility,
        created=NOW,
        updated=NOW,
        documents=1,
    )


@pytest.fixture
def mock_document_repository():
    mock_document_repository = create_autospec(DocumentRepository, instance=True, spec_set=True)
    mock_document_repository.get_document.return_value = DOCUMENT
    mock_document_repository.delete_document.return_value = None
    return mock_document_repository


@pytest.fixture
def mock_collection_query():
    mock_collection_query = create_autospec(CollectionQuery, instance=True, spec_set=True)
    mock_collection_query.get_collection.return_value = _collection_view()
    return mock_collection_query


@pytest.fixture
def mock_chunk_index():
    mock_chunk_index = create_autospec(ChunkIndex, instance=True, spec_set=True)
    mock_chunk_index.delete_document_chunks.return_value = None
    return mock_chunk_index


@pytest.fixture
def use_case(mock_document_repository, mock_collection_query, mock_chunk_index):
    return DeleteDocumentUseCase(document_repository=mock_document_repository, collection_query=mock_collection_query, chunk_index=mock_chunk_index)


class TestDeleteDocumentUseCase:
    async def test_should_delete_chunks_and_document(self, use_case, mock_document_repository, mock_chunk_index):
        # Act
        result = await use_case.execute(DeleteDocumentCommand(user_id=OWNER_ID, document_id=DOCUMENT_ID))

        # Assert
        assert result == DeleteDocumentUseCaseSuccess()
        mock_chunk_index.delete_document_chunks.assert_awaited_once_with(document_id=DOCUMENT_ID)
        mock_document_repository.delete_document.assert_awaited_once_with(document_id=DOCUMENT_ID)

    async def test_should_keep_document_when_chunk_deletion_fails(self, use_case, mock_document_repository, mock_chunk_index):
        # Arrange
        mock_chunk_index.delete_document_chunks.side_effect = httpx.ConnectError("Meilisearch is unreachable")

        # Act
        with pytest.raises(httpx.ConnectError):
            await use_case.execute(DeleteDocumentCommand(user_id=OWNER_ID, document_id=DOCUMENT_ID))

        # Assert
        mock_document_repository.delete_document.assert_not_awaited()

    async def test_should_return_document_not_found_error_when_document_does_not_exist(self, use_case, mock_document_repository, mock_collection_query):  # fmt: off
        # Arrange
        mock_document_repository.get_document.return_value = DocumentNotFoundError()

        # Act
        result = await use_case.execute(DeleteDocumentCommand(user_id=OWNER_ID, document_id=DOCUMENT_ID))

        # Assert
        assert result == DocumentNotFoundError()
        mock_collection_query.get_collection.assert_not_awaited()

    async def test_should_return_document_not_found_error_when_collection_does_not_exist(self, use_case, mock_collection_query, mock_chunk_index):  # fmt: off
        # Arrange
        mock_collection_query.get_collection.return_value = CollectionNotFoundError()

        # Act
        result = await use_case.execute(DeleteDocumentCommand(user_id=OWNER_ID, document_id=DOCUMENT_ID))

        # Assert
        assert result == DocumentNotFoundError()
        mock_chunk_index.delete_document_chunks.assert_not_awaited()

    async def test_should_return_document_not_found_error_when_collection_is_private_and_not_owned(self, use_case, mock_chunk_index):  # fmt: off
        # Act
        result = await use_case.execute(DeleteDocumentCommand(user_id=OTHER_USER_ID, document_id=DOCUMENT_ID))

        # Assert
        assert result == DocumentNotFoundError()
        mock_chunk_index.delete_document_chunks.assert_not_awaited()

    async def test_should_return_document_not_found_error_when_collection_is_public_but_not_owned(self, use_case, mock_collection_query, mock_chunk_index):  # fmt: off
        # Arrange
        mock_collection_query.get_collection.return_value = _collection_view(CollectionVisibility.PUBLIC)

        # Act
        result = await use_case.execute(DeleteDocumentCommand(user_id=OTHER_USER_ID, document_id=DOCUMENT_ID))

        # Assert
        assert result == DocumentNotFoundError()
        mock_chunk_index.delete_document_chunks.assert_not_awaited()

    async def test_should_return_document_not_found_error_when_document_is_deleted_concurrently(self, use_case, mock_document_repository):  # fmt: off
        # Arrange
        mock_document_repository.delete_document.return_value = DocumentNotFoundError()

        # Act
        result = await use_case.execute(DeleteDocumentCommand(user_id=OWNER_ID, document_id=DOCUMENT_ID))

        # Assert
        assert result == DocumentNotFoundError()
