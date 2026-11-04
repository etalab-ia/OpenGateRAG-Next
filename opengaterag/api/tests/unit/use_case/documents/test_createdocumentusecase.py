from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import create_autospec

import pytest

from opengaterag.api.domain.collection import CollectionQuery
from opengaterag.api.domain.collection.entities import CollectionVisibility
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.domain.collection.views import CollectionView
from opengaterag.api.domain.document import DocumentParser, DocumentRepository, TextSplitter
from opengaterag.api.domain.document.entities import Chunk, Document
from opengaterag.api.domain.document.errors import UnsupportedFileTypeError
from opengaterag.api.domain.search import ChunkIndex
from opengaterag.api.domain.search.errors import ChunkEmbeddingFailedError
from opengaterag.api.use_cases.documents import CreateDocumentCommand, CreateDocumentUseCase, CreateDocumentUseCaseSuccess

OWNER_ID = 1
OTHER_USER_ID = 2
COLLECTION_ID = 7
DOCUMENT_ID = 42
NOW = datetime(2030, 1, 1, tzinfo=UTC)
METADATA = {"source_title": "Annual report"}

COMMAND = CreateDocumentCommand(
    user_id=OWNER_ID,
    collection_id=COLLECTION_ID,
    name="report.md",
    file_name="report.md",
    content_type="text/markdown",
    content=b"# Report",
    metadata=METADATA,
)
DOCUMENT = Document(id=DOCUMENT_ID, collection_id=COLLECTION_ID, name="report.md", metadata=METADATA, created=NOW)


def _collection_view(visibility: CollectionVisibility = CollectionVisibility.PRIVATE) -> CollectionView:
    return CollectionView(
        id=COLLECTION_ID,
        user_id=OWNER_ID,
        name="my-collection",
        description=None,
        visibility=visibility,
        created=NOW,
        updated=NOW,
        documents=0,
    )


@pytest.fixture
def mock_collection_query():
    mock_collection_query = create_autospec(CollectionQuery, instance=True, spec_set=True)
    mock_collection_query.get_collection.return_value = _collection_view()
    return mock_collection_query


@pytest.fixture
def mock_document_repository():
    mock_document_repository = create_autospec(DocumentRepository, instance=True, spec_set=True)
    mock_document_repository.create_document.return_value = DOCUMENT
    return mock_document_repository


@pytest.fixture
def mock_document_parser():
    mock_document_parser = create_autospec(DocumentParser, instance=True, spec_set=True)
    mock_document_parser.parse.return_value = "# Report\n\nFirst part.\n\nSecond part."
    return mock_document_parser


@pytest.fixture
def mock_text_splitter():
    mock_text_splitter = create_autospec(TextSplitter, instance=True, spec_set=True)
    mock_text_splitter.split.return_value = ["# Report\n\nFirst part.", "Second part."]
    return mock_text_splitter


@pytest.fixture
def mock_chunk_index():
    mock_chunk_index = create_autospec(ChunkIndex, instance=True, spec_set=True)
    mock_chunk_index.add_chunks.return_value = None
    return mock_chunk_index


@pytest.fixture
def use_case(mock_collection_query, mock_document_repository, mock_document_parser, mock_text_splitter, mock_chunk_index):
    return CreateDocumentUseCase(
        collection_query=mock_collection_query,
        document_repository=mock_document_repository,
        document_parser=mock_document_parser,
        text_splitter=mock_text_splitter,
        chunk_index=mock_chunk_index,
    )


class TestCreateDocumentUseCase:
    async def test_should_create_document_and_index_its_chunks(self, use_case, mock_document_repository, mock_chunk_index):
        # Act
        result = await use_case.execute(COMMAND)

        # Assert
        assert result == CreateDocumentUseCaseSuccess(document=DOCUMENT)
        mock_document_repository.create_document.assert_awaited_once_with(collection_id=COLLECTION_ID, name="report.md", metadata=METADATA)
        mock_chunk_index.add_chunks.assert_awaited_once_with(
            chunks=[
                Chunk(document_id=DOCUMENT_ID, collection_id=COLLECTION_ID, position=0, content="# Report\n\nFirst part.", metadata=METADATA),
                Chunk(document_id=DOCUMENT_ID, collection_id=COLLECTION_ID, position=1, content="Second part.", metadata=METADATA),
            ]
        )

    async def test_should_return_collection_not_found_error_when_collection_does_not_exist(self, use_case, mock_collection_query, mock_document_parser):  # fmt: off
        # Arrange
        mock_collection_query.get_collection.return_value = CollectionNotFoundError()

        # Act
        result = await use_case.execute(COMMAND)

        # Assert
        assert result == CollectionNotFoundError()
        mock_document_parser.parse.assert_not_awaited()

    async def test_should_return_collection_not_found_error_when_collection_is_public_but_not_owned(self, use_case, mock_collection_query, mock_document_parser):  # fmt: off
        # Arrange
        mock_collection_query.get_collection.return_value = _collection_view(CollectionVisibility.PUBLIC)

        # Act
        result = await use_case.execute(replace(COMMAND, user_id=OTHER_USER_ID))

        # Assert
        assert result == CollectionNotFoundError()
        mock_document_parser.parse.assert_not_awaited()

    async def test_should_return_unsupported_file_type_error_when_file_cannot_be_parsed(self, use_case, mock_document_parser, mock_document_repository):  # fmt: off
        # Arrange
        mock_document_parser.parse.return_value = UnsupportedFileTypeError()

        # Act
        result = await use_case.execute(COMMAND)

        # Assert
        assert result == UnsupportedFileTypeError()
        mock_document_repository.create_document.assert_not_awaited()

    async def test_should_delete_chunks_and_document_when_embedding_fails(self, use_case, mock_document_repository, mock_chunk_index):
        # Arrange
        mock_chunk_index.add_chunks.return_value = ChunkEmbeddingFailedError()

        # Act
        result = await use_case.execute(COMMAND)

        # Assert
        assert result == ChunkEmbeddingFailedError()
        mock_chunk_index.delete_document_chunks.assert_awaited_once_with(document_id=DOCUMENT_ID)
        mock_document_repository.delete_document.assert_awaited_once_with(document_id=DOCUMENT_ID)
