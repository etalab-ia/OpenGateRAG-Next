from opengaterag.api.domain import BaseModel, UtcDatetime

DocumentMetadata = dict[str, str | int | float | bool]


class Document(BaseModel):
    id: int
    collection_id: int
    name: str
    chunks: int
    metadata: DocumentMetadata
    created: UtcDatetime


class Chunk(BaseModel):
    document_id: int
    collection_id: int
    position: int
    content: str
    metadata: DocumentMetadata
