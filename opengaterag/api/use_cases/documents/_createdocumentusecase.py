from dataclasses import dataclass

from opengaterag.api.domain.collection import CollectionQuery
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.domain.collection.views import CollectionView
from opengaterag.api.domain.document import DocumentParser, DocumentRepository, TextSplitter
from opengaterag.api.domain.document.entities import Chunk, Document, DocumentMetadata
from opengaterag.api.domain.document.errors import UnsupportedFileTypeError
from opengaterag.api.domain.search import ChunkIndex
from opengaterag.api.domain.search.errors import ChunkEmbeddingFailedError


@dataclass
class CreateDocumentCommand:
    user_id: int
    collection_id: int
    name: str
    file_name: str
    content_type: str | None
    content: bytes
    metadata: DocumentMetadata


@dataclass
class CreateDocumentUseCaseSuccess:
    document: Document


type CreateDocumentUseCaseResult = CreateDocumentUseCaseSuccess | CollectionNotFoundError | UnsupportedFileTypeError | ChunkEmbeddingFailedError


class CreateDocumentUseCase:
    def __init__(
        self,
        collection_query: CollectionQuery,
        document_repository: DocumentRepository,
        document_parser: DocumentParser,
        text_splitter: TextSplitter,
        chunk_index: ChunkIndex,
    ):
        self.collection_query = collection_query
        self.document_repository = document_repository
        self.document_parser = document_parser
        self.text_splitter = text_splitter
        self.chunk_index = chunk_index

    async def execute(self, command: CreateDocumentCommand) -> CreateDocumentUseCaseResult:
        collection = await self.collection_query.get_collection(collection_id=command.collection_id)

        match collection:
            case CollectionNotFoundError():
                return collection
            case CollectionView() if not collection.is_writable_by(user_id=command.user_id):
                return CollectionNotFoundError()

        text = await self.document_parser.parse(file_name=command.file_name, content_type=command.content_type, content=command.content)

        match text:
            case UnsupportedFileTypeError():
                return text

        contents = self.text_splitter.split(text=text)
        document = await self.document_repository.create_document(collection_id=command.collection_id, name=command.name, metadata=command.metadata)
        chunks = [
            Chunk(document_id=document.id, collection_id=document.collection_id, position=position, content=content, metadata=document.metadata)
            for position, content in enumerate(contents)
        ]
        indexed = await self.chunk_index.add_chunks(chunks=chunks)

        match indexed:
            case ChunkEmbeddingFailedError():
                await self.chunk_index.delete_document_chunks(document_id=document.id)
                await self.document_repository.delete_document(document_id=document.id)
                return indexed
            case None:
                return CreateDocumentUseCaseSuccess(document=document)
