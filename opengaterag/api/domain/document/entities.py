from opengaterag.api.domain import BaseModel, UtcDatetime

DocumentAttributes = dict[str, str | int | float | bool]


class Document(BaseModel):
    id: int
    collection_id: int
    name: str
    attributes: DocumentAttributes
    created: UtcDatetime


class Chunk(BaseModel):
    document_id: int
    collection_id: int
    position: int
    content: str
    attributes: DocumentAttributes
