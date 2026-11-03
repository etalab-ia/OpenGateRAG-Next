from unittest.mock import create_autospec

from fastapi import FastAPI
from httpx import AsyncClient
import pytest

from opengaterag.api.dependencies import get_documents_use_case_factory
from opengaterag.api.domain.collection.entities import CollectionVisibility
from opengaterag.api.domain.collection.errors import CollectionNotFoundError
from opengaterag.api.infrastructure.fastapi.routes import EndpointRoute
from opengaterag.api.infrastructure.postgres.models import Collection as CollectionTable
from opengaterag.api.infrastructure.postgres.models import Document as DocumentTable
from opengaterag.api.tests.integration.endpoints.conftest import API_KEY, AUTHENTICATED_USER_ID
from opengaterag.api.use_cases.documents import GetDocumentsUseCase

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def _url(collection_id: int) -> str:
    return f"/v1{EndpointRoute.COLLECTION_DOCUMENTS.format(collection_id=collection_id)}"


class TestGetDocuments:
    async def test_should_get_paginated_list_of_documents_of_own_collection(self, client: AsyncClient, db_session, mock_authenticated_user_query):  # fmt: off
        # Arrange
        collection = CollectionTable(user_id=AUTHENTICATED_USER_ID, name="my-collection", description=None, visibility=CollectionVisibility.PRIVATE)  # fmt: off
        db_session.add(collection)
        await db_session.flush()
        first = DocumentTable(collection_id=collection.id, name="first.pdf")
        second = DocumentTable(collection_id=collection.id, name="second.pdf")
        db_session.add_all([first, second])
        await db_session.flush()

        # Act
        response = await client.get(url=_url(collection.id), headers=HEADERS, params={"offset": 0, "limit": 1})

        # Assert
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["object"] == "list"
        assert (body["total"], body["offset"], body["limit"]) == (2, 0, 1)
        assert [document["id"] for document in body["data"]] == [first.id]
        assert body["data"][0]["object"] == "document"

    @pytest.mark.parametrize(
        "use_case_result,expected_status,expected_detail",
        [
            (CollectionNotFoundError(), 404, "Collection not found."),
        ],
    )
    async def test_should_map_error_to_http_status(
        self, client: AsyncClient, app: FastAPI, mock_authenticated_user_query, use_case_result, expected_status, expected_detail
    ):
        # Arrange
        mock_use_case = create_autospec(GetDocumentsUseCase, instance=True, spec_set=True)
        mock_use_case.execute.return_value = use_case_result
        app.dependency_overrides[get_documents_use_case_factory] = lambda: mock_use_case

        # Act
        response = await client.get(url=_url(7), headers=HEADERS)

        # Assert
        assert response.status_code == expected_status, response.text
        assert response.json()["detail"] == expected_detail
