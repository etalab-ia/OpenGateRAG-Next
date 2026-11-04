from unittest.mock import create_autospec

from fastapi import FastAPI
from httpx import AsyncClient
import pytest

from opengaterag.api.dependencies import delete_collection_use_case_factory
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.infrastructure.fastapi.routes import EndpointRoute
from opengaterag.api.tests.integration.endpoints.conftest import API_KEY, AUTHENTICATED_USER_ID
from opengaterag.api.use_cases.collections import DeleteCollectionCommand, DeleteCollectionUseCase, DeleteCollectionUseCaseSuccess

HEADERS = {"Authorization": f"Bearer {API_KEY}"}
COLLECTION_ID = 7
URL = f"/v1{EndpointRoute.COLLECTION.format(collection_id=COLLECTION_ID)}"


@pytest.fixture
def mock_use_case(app: FastAPI):
    mock_use_case = create_autospec(DeleteCollectionUseCase, instance=True, spec_set=True)
    app.dependency_overrides[delete_collection_use_case_factory] = lambda: mock_use_case

    return mock_use_case


class TestDeleteCollection:
    async def test_should_delete_collection(self, client: AsyncClient, mock_authenticated_user_query, mock_use_case):
        # Arrange
        mock_use_case.execute.return_value = DeleteCollectionUseCaseSuccess()

        # Act
        response = await client.delete(url=URL, headers=HEADERS)

        # Assert
        assert response.status_code == 204, response.text
        mock_use_case.execute.assert_awaited_once_with(DeleteCollectionCommand(user_id=AUTHENTICATED_USER_ID, collection_id=COLLECTION_ID))

    @pytest.mark.parametrize(
        "use_case_result,expected_status,expected_detail",
        [
            (CollectionNotFoundError(), 404, "Collection not found."),
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
