from dataclasses import dataclass

from opengaterag.api.domain.collection import CollectionQuery
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.domain.collection.views import CollectionView
from opengaterag.api.domain.document import DocumentRepository
from opengaterag.api.domain.document.errors import DocumentNotFoundError
from opengaterag.api.domain.search import ChunkIndex


@dataclass
class DeleteDocumentCommand:
    user_id: int
    document_id: int


@dataclass
class DeleteDocumentUseCaseSuccess:
    pass


type DeleteDocumentUseCaseResult = DeleteDocumentUseCaseSuccess | DocumentNotFoundError


class DeleteDocumentUseCase:
    def __init__(self, document_repository: DocumentRepository, collection_query: CollectionQuery, chunk_index: ChunkIndex):
        self.document_repository = document_repository
        self.collection_query = collection_query
        self.chunk_index = chunk_index

    async def execute(self, command: DeleteDocumentCommand) -> DeleteDocumentUseCaseResult:
        document = await self.document_repository.get_document(document_id=command.document_id)

        match document:
            case DocumentNotFoundError():
                return document

        collection = await self.collection_query.get_collection(collection_id=document.collection_id)

        match collection:
            case CollectionNotFoundError():
                return DocumentNotFoundError()
            case CollectionView() if not collection.is_writable_by(user_id=command.user_id):
                return DocumentNotFoundError()

        # Chunks first: if the Postgres delete then fails, the document stays visible and can be deleted again,
        # whereas the reverse order would leave chunks that search still returns.
        await self.chunk_index.delete_document_chunks(document_id=document.id)
        deleted = await self.document_repository.delete_document(document_id=document.id)

        match deleted:
            case DocumentNotFoundError():
                return deleted
            case None:
                return DeleteDocumentUseCaseSuccess()
