from datetime import UTC, datetime
from unittest.mock import create_autospec

from fastapi import FastAPI
from httpx import AsyncClient
import pytest

from opengaterag.api.dependencies import create_document_use_case_factory
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.domain.document.entities import Document
from opengaterag.api.domain.document.errors import UnsupportedFileTypeError
from opengaterag.api.domain.search.errors import ChunkEmbeddingFailedError
from opengaterag.api.infrastructure.fastapi.routes import EndpointRoute
from opengaterag.api.tests.integration.endpoints.conftest import API_KEY, AUTHENTICATED_USER_ID
from opengaterag.api.use_cases.documents import CreateDocumentCommand, CreateDocumentUseCase, CreateDocumentUseCaseSuccess

HEADERS = {"Authorization": f"Bearer {API_KEY}"}
COLLECTION_ID = 7
URL = f"/v1{EndpointRoute.COLLECTION_DOCUMENTS.format(collection_id=COLLECTION_ID)}"
FILES = {"file": ("report.md", b"# Report", "text/markdown")}


@pytest.fixture
def mock_use_case(app: FastAPI):
    mock_use_case = create_autospec(CreateDocumentUseCase, instance=True, spec_set=True)
    app.dependency_overrides[create_document_use_case_factory] = lambda: mock_use_case

    return mock_use_case


class TestCreateDocument:
    async def test_should_create_document_from_uploaded_file(self, client: AsyncClient, mock_authenticated_user_query, mock_use_case):
        # Arrange
        document = Document(id=42, collection_id=COLLECTION_ID, name="report.md", metadata={"year": 2030}, created=datetime.now(UTC))
        mock_use_case.execute.return_value = CreateDocumentUseCaseSuccess(document=document)

        # Act
        response = await client.post(url=URL, headers=HEADERS, files=FILES, data={"metadata": '{"year": 2030}'})

        # Assert
        assert response.status_code == 201, response.text
        assert response.json()["id"] == 42
        mock_use_case.execute.assert_awaited_once_with(
            CreateDocumentCommand(
                user_id=AUTHENTICATED_USER_ID,
                collection_id=COLLECTION_ID,
                name="report.md",
                file_name="report.md",
                content_type="text/markdown",
                content=b"# Report",
                metadata={"year": 2030},
            )
        )

    @pytest.mark.parametrize(
        "use_case_result,expected_status,expected_detail",
        [
            (CollectionNotFoundError(), 404, "Collection not found."),
            (UnsupportedFileTypeError(), 415, "Unsupported file type. Upload a Markdown or plain text file."),
            (ChunkEmbeddingFailedError(), 502, "The embedding of the document failed."),
        ],
    )
    async def test_should_map_error_to_http_status(
        self, client: AsyncClient, mock_authenticated_user_query, mock_use_case, use_case_result, expected_status, expected_detail
    ):
        # Arrange
        mock_use_case.execute.return_value = use_case_result

        # Act
        response = await client.post(url=URL, headers=HEADERS, files=FILES)

        # Assert
        assert response.status_code == expected_status, response.text
        assert response.json()["detail"] == expected_detail
