from datetime import UTC, datetime
from unittest.mock import create_autospec

import pytest

from opengaterag.api.domain.collection import CollectionQuery
from opengaterag.api.domain.collection.entities import CollectionVisibility
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.domain.collection.views import CollectionView
from opengaterag.api.domain.document import DocumentRepository
from opengaterag.api.domain.document.entities import Document
from opengaterag.api.use_cases.documents import GetDocumentsCommand, GetDocumentsUseCase, GetDocumentsUseCaseSuccess

OWNER_ID = 1
OTHER_USER_ID = 2
COLLECTION_ID = 7
NOW = datetime(2030, 1, 1, tzinfo=UTC)

DOCUMENT = Document(id=42, collection_id=COLLECTION_ID, name="document.pdf", attributes={}, created=NOW)


def _collection_view(visibility: CollectionVisibility) -> CollectionView:
    return CollectionView(
        id=COLLECTION_ID,
        user_id=OWNER_ID,
        name="my-collection",
        description=None,
        visibility=visibility,
        created=NOW,
        updated=NOW,
        documents=12,
    )


@pytest.fixture
def mock_document_repository():
    return create_autospec(DocumentRepository, instance=True, spec_set=True)


@pytest.fixture
def mock_collection_query():
    return create_autospec(CollectionQuery, instance=True, spec_set=True)


@pytest.fixture
def use_case(mock_document_repository, mock_collection_query):
    return GetDocumentsUseCase(document_repository=mock_document_repository, collection_query=mock_collection_query)


class TestGetDocumentsUseCase:
    async def test_should_return_page_of_documents_of_readable_collection(self, use_case, mock_document_repository, mock_collection_query):
        # Arrange
        mock_collection_query.get_collection.return_value = _collection_view(CollectionVisibility.PRIVATE)
        mock_document_repository.get_documents.return_value = ([DOCUMENT], 12)

        # Act
        result = await use_case.execute(GetDocumentsCommand(user_id=OWNER_ID, collection_id=COLLECTION_ID, offset=5, limit=1))

        # Assert
        assert result == GetDocumentsUseCaseSuccess(data=[DOCUMENT], total=12, offset=5, limit=1)
        mock_document_repository.get_documents.assert_awaited_once_with(collection_id=COLLECTION_ID, offset=5, limit=1)

    async def test_should_return_collection_not_found_error_when_collection_is_not_readable(self, use_case, mock_document_repository, mock_collection_query):  # fmt: off
        # Arrange
        mock_collection_query.get_collection.return_value = _collection_view(CollectionVisibility.PRIVATE)

        # Act
        result = await use_case.execute(GetDocumentsCommand(user_id=OTHER_USER_ID, collection_id=COLLECTION_ID, offset=0, limit=10))

        # Assert
        assert result == CollectionNotFoundError()
        mock_document_repository.get_documents.assert_not_awaited()

    async def test_should_return_collection_not_found_error_when_collection_does_not_exist(self, use_case, mock_document_repository, mock_collection_query):  # fmt: off
        # Arrange
        mock_collection_query.get_collection.return_value = CollectionNotFoundError()

        # Act
        result = await use_case.execute(GetDocumentsCommand(user_id=OWNER_ID, collection_id=COLLECTION_ID, offset=0, limit=10))

        # Assert
        assert result == CollectionNotFoundError()
        mock_document_repository.get_documents.assert_not_awaited()
