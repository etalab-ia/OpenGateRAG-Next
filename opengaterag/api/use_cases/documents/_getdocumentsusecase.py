from dataclasses import dataclass

from opengaterag.api.domain.collection import CollectionQuery
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.domain.collection.views import CollectionView
from opengaterag.api.domain.document import DocumentRepository
from opengaterag.api.domain.document.entities import Document


@dataclass
class GetDocumentsCommand:
    user_id: int
    collection_id: int
    offset: int
    limit: int


@dataclass
class GetDocumentsUseCaseSuccess:
    data: list[Document]
    total: int
    offset: int
    limit: int


type GetDocumentsUseCaseResult = GetDocumentsUseCaseSuccess | CollectionNotFoundError


class GetDocumentsUseCase:
    def __init__(self, document_repository: DocumentRepository, collection_query: CollectionQuery):
        self.document_repository = document_repository
        self.collection_query = collection_query

    async def execute(self, command: GetDocumentsCommand) -> GetDocumentsUseCaseResult:
        collection = await self.collection_query.get_collection(collection_id=command.collection_id)

        match collection:
            case CollectionNotFoundError():
                return collection
            case CollectionView() if not collection.is_readable_by(user_id=command.user_id):
                return CollectionNotFoundError()

        documents, total = await self.document_repository.get_documents(
            collection_id=command.collection_id,
            offset=command.offset,
            limit=command.limit,
        )

        return GetDocumentsUseCaseSuccess(data=documents, total=total, offset=command.offset, limit=command.limit)
