from typing import Annotated, Literal

from fastapi import UploadFile
from pydantic import Field, Json, StringConstraints

from opengaterag.api.domain import BaseModel
from opengaterag.api.domain.document.entities import DocumentAttributes
from opengaterag.api.infrastructure.fastapi.schemas import UnixTimestamp

# Keys end up in Meilisearch filters as `attributes.<key>`, so they are restricted to characters that need no quoting there.
AttributeKey = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_]{1,64}$")]


class CreateDocumentBody(BaseModel):
    file: Annotated[UploadFile, Field(description="File to upload: Markdown or plain text.")]
    name: Annotated[str | None, StringConstraints(strip_whitespace=True, min_length=1), Field(default=None, description="Name of the document. Defaults to the file name.")]  # fmt: off
    attributes: Annotated[Json[dict[AttributeKey, str | int | float | bool]] | None, Field(default=None, description="Attributes of the document, copied onto each of its chunks to filter searches, as a JSON object of scalar values. Keys contain only letters, digits and underscores.", examples=['{"source_title": "Annual report"}'])]  # fmt: off


class DocumentResponse(BaseModel):
    object: Annotated[Literal["document"], Field(default="document", description="Type of the object.")]
    id: Annotated[int, Field(description="ID of the document.")]
    collection_id: Annotated[int, Field(description="ID of the collection that contains the document.")]
    name: Annotated[str, Field(description="Name of the document.")]
    attributes: Annotated[DocumentAttributes, Field(description="Attributes of the document, copied onto each of its chunks to filter searches.")]
    created: Annotated[UnixTimestamp, Field(description="Time of creation, as Unix timestamp.")]


class DocumentsResponse(BaseModel):
    object: Annotated[Literal["list"], Field(default="list", description="Type of the object.")]
    total: Annotated[int, Field(description="Total number of documents in the collection.")]
    offset: Annotated[int, Field(description="Number of documents skipped.")]
    limit: Annotated[int, Field(description="Maximum number of documents returned.")]
    data: Annotated[list[DocumentResponse], Field(description="The documents of this page.")]
