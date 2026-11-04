from unittest.mock import create_autospec

from fastapi import FastAPI
from httpx import AsyncClient
import pytest

from opengaterag.api.dependencies import delete_document_use_case_factory
from opengaterag.api.domain.document.errors import DocumentNotFoundError
from opengaterag.api.infrastructure.fastapi.routes import EndpointRoute
from opengaterag.api.tests.integration.endpoints.conftest import API_KEY, AUTHENTICATED_USER_ID
from opengaterag.api.use_cases.documents import DeleteDocumentCommand, DeleteDocumentUseCase, DeleteDocumentUseCaseSuccess

HEADERS = {"Authorization": f"Bearer {API_KEY}"}
DOCUMENT_ID = 42
URL = f"/v1{EndpointRoute.DOCUMENT.format(document_id=DOCUMENT_ID)}"


@pytest.fixture
def mock_use_case(app: FastAPI):
    mock_use_case = create_autospec(DeleteDocumentUseCase, instance=True, spec_set=True)
    app.dependency_overrides[delete_document_use_case_factory] = lambda: mock_use_case

    return mock_use_case


class TestDeleteDocument:
    async def test_should_delete_document(self, client: AsyncClient, mock_authenticated_user_query, mock_use_case):
        # Arrange
        mock_use_case.execute.return_value = DeleteDocumentUseCaseSuccess()

        # Act
        response = await client.delete(url=URL, headers=HEADERS)

        # Assert
        assert response.status_code == 204, response.text
        mock_use_case.execute.assert_awaited_once_with(DeleteDocumentCommand(user_id=AUTHENTICATED_USER_ID, document_id=DOCUMENT_ID))

    @pytest.mark.parametrize(
        "use_case_result,expected_status,expected_detail",
        [
            (DocumentNotFoundError(), 404, "Document not found."),
        ],
    )
    async def test_should_map_error_to_http_status(
        self, client: AsyncClient, mock_authenticated_user_query, mock_use_case, use_case_result, expected_status, expected_detail
    ):
        # Arrange
        mock_use_case.execute.return_value = use_case_result

        # Act
        response = await client.delete(url=URL, headers=HEADERS)

        # Assert
        assert response.status_code == expected_status, response.text
        assert response.json()["detail"] == expected_detail
