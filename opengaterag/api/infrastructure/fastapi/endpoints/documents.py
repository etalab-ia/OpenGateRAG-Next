from fastapi import APIRouter, Depends, File, Path, Query, Security

from opengaterag.api.dependencies import create_document_use_case_factory, get_documents_use_case_factory, get_one_document_use_case_factory
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.domain.document.errors import DocumentNotFoundError, UnsupportedFileTypeError
from opengaterag.api.domain.search.errors import ChunkEmbeddingFailedError
from opengaterag.api.domain.user.views import AuthenticatedUserView
from opengaterag.api.infrastructure.fastapi.accesscontroller import AccessController
from opengaterag.api.infrastructure.fastapi.endpoints.exceptions import (
    ChunkEmbeddingFailedHTTPException,
    CollectionNotFoundHTTPException,
    DocumentNotFoundHTTPException,
    UnsupportedFileTypeHTTPException,
)
from opengaterag.api.infrastructure.fastapi.routes import EndpointRoute, RouterName
from opengaterag.api.infrastructure.fastapi.schemas.documents import CreateDocumentBody, DocumentResponse, DocumentsResponse
from opengaterag.api.use_cases.documents import (
    CreateDocumentCommand,
    CreateDocumentUseCase,
    CreateDocumentUseCaseSuccess,
    GetDocumentsCommand,
    GetDocumentsUseCase,
    GetDocumentsUseCaseSuccess,
    GetOneDocumentCommand,
    GetOneDocumentUseCase,
    GetOneDocumentUseCaseSuccess,
)

router = APIRouter(prefix="/v1", tags=[RouterName.DOCUMENTS.title()])


@router.post(path=EndpointRoute.COLLECTION_DOCUMENTS, status_code=201)
async def create_document(
    collection_id: int = Path(description="ID of the collection."),
    # `File`, not `Form`: FastAPI documents a form model as `multipart/form-data` only when it is declared with `File`.
    body: CreateDocumentBody = File(description="The document creation request."),
    user: AuthenticatedUserView = Security(AccessController()),
    create_document_use_case: CreateDocumentUseCase = Depends(create_document_use_case_factory),
) -> DocumentResponse:
    """
    Upload a file to a collection you own. The file is split into chunks, which are embedded and indexed for search.
    """
    command = CreateDocumentCommand(
        user_id=user.id,
        collection_id=collection_id,
        name=body.name or body.file.filename,
        file_name=body.file.filename,
        content_type=body.file.content_type,
        content=await body.file.read(),
        metadata=body.metadata or {},
    )
    result = await create_document_use_case.execute(command)

    match result:
        case CreateDocumentUseCaseSuccess(document=document):
            return DocumentResponse.model_validate(document, from_attributes=True)
        case CollectionNotFoundError():
            raise CollectionNotFoundHTTPException()
        case UnsupportedFileTypeError():
            raise UnsupportedFileTypeHTTPException()
        case ChunkEmbeddingFailedError():
            raise ChunkEmbeddingFailedHTTPException()


@router.get(path=EndpointRoute.COLLECTION_DOCUMENTS)
async def get_documents(
    collection_id: int = Path(description="ID of the collection."),
    offset: int = Query(default=0, ge=0, description="Number of documents to skip."),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of documents to return."),
    user: AuthenticatedUserView = Security(AccessController()),
    get_documents_use_case: GetDocumentsUseCase = Depends(get_documents_use_case_factory),
) -> DocumentsResponse:
    """
    Get the documents of a collection you own or of a public collection.
    """
    command = GetDocumentsCommand(user_id=user.id, collection_id=collection_id, offset=offset, limit=limit)
    result = await get_documents_use_case.execute(command)

    match result:
        case GetDocumentsUseCaseSuccess():
            return DocumentsResponse.model_validate(result, from_attributes=True)
        case CollectionNotFoundError():
            raise CollectionNotFoundHTTPException()


@router.get(path=EndpointRoute.DOCUMENT)
async def get_one_document(
    document_id: int = Path(description="ID of the document."),
    user: AuthenticatedUserView = Security(AccessController()),
    get_one_document_use_case: GetOneDocumentUseCase = Depends(get_one_document_use_case_factory),
) -> DocumentResponse:
    """
    Get a document from a collection you own or from a public collection.
    """
    command = GetOneDocumentCommand(user_id=user.id, document_id=document_id)
    result = await get_one_document_use_case.execute(command)

    match result:
        case GetOneDocumentUseCaseSuccess(document=document):
            return DocumentResponse.model_validate(document, from_attributes=True)
        case DocumentNotFoundError():
            raise DocumentNotFoundHTTPException()
