import asyncio
from typing import Any

import httpx

FINISHED_TASK_STATUSES = ("succeeded", "failed", "canceled")
TASK_POLL_INTERVAL_SECONDS = 0.05


async def wait_for_task(meilisearch_client: httpx.AsyncClient, task_uid: int, task_timeout: int) -> dict[str, Any]:
    """Return the task once it has finished, whatever its status. Raise `TimeoutError` if it has not finished within `task_timeout` seconds."""
    async with asyncio.timeout(task_timeout):
        while True:
            response = await meilisearch_client.get(f"/tasks/{task_uid}")
            response.raise_for_status()
            task = response.json()
            if task["status"] in FINISHED_TASK_STATUSES:
                return task
            await asyncio.sleep(TASK_POLL_INTERVAL_SECONDS)


def raise_unsuccessful_task(task: dict[str, Any]) -> None:
    if task["status"] != "succeeded":
        raise RuntimeError(f"Meilisearch task {task['uid']} ({task['type']}) ended as {task['status']}: {(task.get('error') or {}).get('message')}")
