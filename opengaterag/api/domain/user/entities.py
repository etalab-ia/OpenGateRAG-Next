from opengaterag.api.domain import BaseModel, UtcDatetime


class User(BaseModel):
    id: int
    storage_limit: int | None
    create_public_collection: bool
    created: UtcDatetime
    updated: UtcDatetime

    def has_storage_for(self, used_storage: int, size: int) -> bool:
        return self.storage_limit is None or used_storage + size <= self.storage_limit
