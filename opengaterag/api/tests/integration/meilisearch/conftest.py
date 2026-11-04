from collections.abc import AsyncGenerator
import os
from uuid import uuid4

import httpx
import pytest_asyncio

from opengaterag.api.infrastructure.meilisearch._meilisearchtask import raise_unsuccessful_task, wait_for_task

TEST_MEILISEARCH_URL = os.getenv("TEST_MEILISEARCH_URL", "http://localhost:7700")
TEST_MEILISEARCH_API_KEY = os.getenv("TEST_MEILISEARCH_API_KEY", "changemechangeme")
TASK_TIMEOUT = 30


@pytest_asyncio.fixture
async def meilisearch_client() -> AsyncGenerator[httpx.AsyncClient]:
    async with httpx.AsyncClient(base_url=TEST_MEILISEARCH_URL, headers={"Authorization": f"Bearer {TEST_MEILISEARCH_API_KEY}"}) as client:
        yield client


@pytest_asyncio.fixture
async def index_name(meilisearch_client: httpx.AsyncClient) -> AsyncGenerator[str]:
    """A new index for each test, with the filterable attributes of the real index but no embedder, so that adding chunks does not call OpenGateLLM."""
    index_name = f"test-{uuid4().hex}"
    response = await meilisearch_client.post("/indexes", json={"uid": index_name, "primaryKey": "id"})
    response.raise_for_status()
    response = await meilisearch_client.patch(f"/indexes/{index_name}/settings", json={"filterableAttributes": ["collection_id", "document_id", "attributes"]})  # fmt: off
    response.raise_for_status()
    raise_unsuccessful_task(await wait_for_task(meilisearch_client, task_uid=response.json()["taskUid"], task_timeout=TASK_TIMEOUT))

    yield index_name

    await meilisearch_client.delete(f"/indexes/{index_name}")
