from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from opengaterag.api.domain.document import DocumentRepository
from opengaterag.api.domain.document.entities import Document, DocumentMetadata
from opengaterag.api.domain.document.errors import DocumentNotFoundError
from opengaterag.api.infrastructure.postgres.models import Document as DocumentTable

# Selected as table columns so that rows expose `metadata` under its column name, not the `metadata_` attribute.
DOCUMENT_COLUMNS = DocumentTable.__table__.columns


class PostgresDocumentRepository(DocumentRepository):
    def __init__(self, postgres_session: AsyncSession):
        self.postgres_session = postgres_session

    async def create_document(self, collection_id: int, name: str, metadata: DocumentMetadata) -> Document:
        statement = insert(DocumentTable).values(collection_id=collection_id, name=name, metadata_=metadata).returning(*DOCUMENT_COLUMNS)  # fmt: off
        row = (await self.postgres_session.execute(statement)).one()

        return Document.model_validate(row, from_attributes=True)

    async def get_document(self, document_id: int) -> Document | DocumentNotFoundError:
        statement = select(*DOCUMENT_COLUMNS).where(DocumentTable.id == document_id)
        row = (await self.postgres_session.execute(statement)).one_or_none()

        if row is None:
            return DocumentNotFoundError()

        return Document.model_validate(row, from_attributes=True)

    async def get_documents(self, collection_id: int, offset: int, limit: int) -> tuple[list[Document], int]:
        total = await self.postgres_session.scalar(select(func.count()).select_from(DocumentTable).where(DocumentTable.collection_id == collection_id))  # fmt: off
        statement = select(*DOCUMENT_COLUMNS).where(DocumentTable.collection_id == collection_id).order_by(DocumentTable.id).offset(offset).limit(limit)  # fmt: off
        rows = (await self.postgres_session.execute(statement)).all()

        return [Document.model_validate(row, from_attributes=True) for row in rows], total

    async def delete_document(self, document_id: int) -> None | DocumentNotFoundError:
        statement = delete(DocumentTable).where(DocumentTable.id == document_id).returning(DocumentTable.id)
        deleted_id = (await self.postgres_session.execute(statement)).scalar_one_or_none()

        if deleted_id is None:
            return DocumentNotFoundError()

        return None
