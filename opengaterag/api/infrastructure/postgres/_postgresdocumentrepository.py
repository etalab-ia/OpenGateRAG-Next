from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from opengaterag.api.domain.document import DocumentRepository
from opengaterag.api.domain.document.entities import Document
from opengaterag.api.domain.document.errors import DocumentNotFoundError
from opengaterag.api.infrastructure.postgres.models import Document as DocumentTable


class PostgresDocumentRepository(DocumentRepository):
    def __init__(self, postgres_session: AsyncSession):
        self.postgres_session = postgres_session

    async def get_document(self, document_id: int) -> Document | DocumentNotFoundError:
        statement = select(DocumentTable).where(DocumentTable.id == document_id)
        row = (await self.postgres_session.execute(statement)).scalar_one_or_none()

        if row is None:
            return DocumentNotFoundError()

        return Document.model_validate(row, from_attributes=True)

    async def get_documents(self, collection_id: int, offset: int, limit: int) -> tuple[list[Document], int]:
        total = await self.postgres_session.scalar(select(func.count()).select_from(DocumentTable).where(DocumentTable.collection_id == collection_id))  # fmt: off
        statement = select(DocumentTable).where(DocumentTable.collection_id == collection_id).order_by(DocumentTable.id).offset(offset).limit(limit)  # fmt: off
        rows = (await self.postgres_session.execute(statement)).scalars().all()

        return [Document.model_validate(row, from_attributes=True) for row in rows], total
