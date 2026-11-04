from sqlalchemy import select

from opengaterag.api.domain.collection.entities import CollectionVisibility
from opengaterag.api.domain.document.entities import Document
from opengaterag.api.domain.document.errors import DocumentNotFoundError
from opengaterag.api.infrastructure.postgres import PostgresDocumentRepository
from opengaterag.api.infrastructure.postgres.models import Collection as CollectionTable
from opengaterag.api.infrastructure.postgres.models import Document as DocumentTable


async def _add_collection(db_session, user_id: int = 42) -> int:
    collection = CollectionTable(user_id=user_id, name="my-collection", description=None, visibility=CollectionVisibility.PRIVATE)
    db_session.add(collection)
    await db_session.flush()

    return collection.id


class TestCreateDocument:
    async def test_should_persist_document_with_its_metadata(self, db_session):
        # Arrange
        repository = PostgresDocumentRepository(postgres_session=db_session)
        collection_id = await _add_collection(db_session)

        # Act
        document = await repository.create_document(collection_id=collection_id, name="report.md", metadata={"source_title": "Report", "year": 2030})  # fmt: off

        # Assert
        assert isinstance(document, Document)
        assert document.metadata == {"source_title": "Report", "year": 2030}
        assert document.created.tzinfo is not None


class TestDeleteDocument:
    async def test_should_delete_document(self, db_session):
        # Arrange
        repository = PostgresDocumentRepository(postgres_session=db_session)
        document = DocumentTable(collection_id=await _add_collection(db_session), name="report.md")
        db_session.add(document)
        await db_session.flush()

        # Act
        result = await repository.delete_document(document_id=document.id)

        # Assert
        assert result is None
        assert await db_session.scalar(select(DocumentTable.id).where(DocumentTable.id == document.id)) is None

    async def test_should_return_document_not_found_error_when_document_does_not_exist(self, db_session):
        # Arrange
        repository = PostgresDocumentRepository(postgres_session=db_session)

        # Act
        result = await repository.delete_document(document_id=999_999)

        # Assert
        assert result == DocumentNotFoundError()


class TestGetDocument:
    async def test_should_read_document(self, db_session):
        # Arrange
        repository = PostgresDocumentRepository(postgres_session=db_session)
        collection = CollectionTable(user_id=42, name="my-collection", description=None, visibility=CollectionVisibility.PRIVATE)
        db_session.add(collection)
        await db_session.flush()
        stored = DocumentTable(collection_id=collection.id, name="document.pdf")
        db_session.add(stored)
        await db_session.flush()

        # Act
        document = await repository.get_document(document_id=stored.id)

        # Assert
        assert isinstance(document, Document)
        assert document.collection_id == collection.id
        assert document.name == "document.pdf"
        assert document.created.tzinfo is not None

    async def test_should_return_document_not_found_error_when_document_does_not_exist(self, db_session):
        # Arrange
        repository = PostgresDocumentRepository(postgres_session=db_session)

        # Act
        result = await repository.get_document(document_id=999_999)

        # Assert
        assert result == DocumentNotFoundError()


class TestGetDocuments:
    async def test_should_return_page_of_documents_of_collection_and_its_total(self, db_session):
        # Arrange
        repository = PostgresDocumentRepository(postgres_session=db_session)
        collection = CollectionTable(user_id=42, name="my-collection", description=None, visibility=CollectionVisibility.PRIVATE)
        other_collection = CollectionTable(user_id=42, name="other-collection", description=None, visibility=CollectionVisibility.PRIVATE)
        db_session.add_all([collection, other_collection])
        await db_session.flush()
        documents = [DocumentTable(collection_id=collection.id, name=f"document-{index}.pdf") for index in range(3)]
        db_session.add_all([*documents, DocumentTable(collection_id=other_collection.id, name="other.pdf")])
        await db_session.flush()

        # Act
        page, total = await repository.get_documents(collection_id=collection.id, offset=1, limit=1)

        # Assert
        assert total == 3
        assert [document.id for document in page] == [documents[1].id]
