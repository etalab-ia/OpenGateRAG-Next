from typing import Annotated, Literal

from fastapi import UploadFile
from pydantic import Field, Json, StringConstraints

from opengaterag.api.domain import BaseModel
from opengaterag.api.domain.document.entities import DocumentMetadata
from opengaterag.api.infrastructure.fastapi.schemas import UnixTimestamp

# Keys end up in Meilisearch filters as `metadata.<key>`, so they are restricted to characters that need no quoting there.
MetadataKey = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_]{1,64}$")]


class CreateDocumentBody(BaseModel):
    file: Annotated[UploadFile, Field(description="File to upload: PDF, HTML, Markdown or plain text.")]
    name: Annotated[str | None, StringConstraints(strip_whitespace=True, min_length=1), Field(default=None, description="Name of the document. Defaults to the file name.")]  # fmt: off
    metadata: Annotated[Json[dict[MetadataKey, str | int | float | bool]] | None, Field(default=None, description="Metadata of the document, copied onto each of its chunks, as a JSON object of scalar values. Keys contain only letters, digits and underscores.", examples=['{"source_title": "Annual report"}'])]  # fmt: off


class DocumentResponse(BaseModel):
    object: Annotated[Literal["document"], Field(default="document", description="Type of the object.")]
    id: Annotated[int, Field(description="ID of the document.")]
    collection_id: Annotated[int, Field(description="ID of the collection that contains the document.")]
    name: Annotated[str, Field(description="Name of the document.")]
    chunks: Annotated[int, Field(description="Number of chunks the document was split into.")]
    metadata: Annotated[DocumentMetadata, Field(description="Metadata of the document, copied onto each of its chunks.")]
    created: Annotated[UnixTimestamp, Field(description="Time of creation, as Unix timestamp.")]


class DocumentsResponse(BaseModel):
    object: Annotated[Literal["list"], Field(default="list", description="Type of the object.")]
    total: Annotated[int, Field(description="Total number of documents in the collection.")]
    offset: Annotated[int, Field(description="Number of documents skipped.")]
    limit: Annotated[int, Field(description="Maximum number of documents returned.")]
    data: Annotated[list[DocumentResponse], Field(description="The documents of this page.")]
