from typing import Any

import httpx

from opengaterag.api.infrastructure.configuration import Configuration
from opengaterag.api.infrastructure.meilisearch._meilisearchtask import raise_unsuccessful_task, wait_for_task

MAX_BYTES_PER_CHARACTER = 4


async def bootstrap_meilisearch_index(meilisearch_client: httpx.AsyncClient, configuration: Configuration) -> None:
    meilisearch = configuration.dependencies.meilisearch

    # When the index already exists, this task just fails. An index's tasks run in order, so the settings task below applies to it.
    response = await meilisearch_client.post("/indexes", json={"uid": meilisearch.index_name, "primaryKey": "id"})
    response.raise_for_status()

    response = await meilisearch_client.patch(f"/indexes/{meilisearch.index_name}/settings", json=build_index_settings(configuration))
    response.raise_for_status()
    task = await wait_for_task(meilisearch_client, task_uid=response.json()["taskUid"], task_timeout=meilisearch.task_timeout)
    raise_unsuccessful_task(task)


def build_index_settings(configuration: Configuration) -> dict[str, Any]:
    meilisearch = configuration.dependencies.meilisearch
    opengatellm = configuration.dependencies.opengatellm

    index_settings = {
        "searchableAttributes": ["content"],
        "filterableAttributes": ["collection_id", "document_id", "metadata"],
        "embedders": {
            meilisearch.embedder_name: {
                "source": "rest",
                "url": meilisearch.embedder_url,
                "apiKey": meilisearch.embedder_api_key,
                "dimensions": opengatellm.model_vector_size,
                "request": {"model": opengatellm.model_name, "input": ["{{text}}", "{{..}}"]},
                "response": {"data": [{"embedding": "{{embedding}}"}, "{{..}}"]},
                "documentTemplate": "{{doc.content}}",
                "documentTemplateMaxBytes": configuration.settings.chunk_max_characters * MAX_BYTES_PER_CHARACTER,
            }
        },
    }
    if meilisearch.index_language:
        index_settings["localizedAttributes"] = [{"attributePatterns": ["content"], "locales": [meilisearch.index_language]}]

    return index_settings
