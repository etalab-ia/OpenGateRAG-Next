from datetime import UTC, datetime

import pytest

from opengaterag.api.domain.user.entities import User

NOW = datetime(2030, 1, 1, tzinfo=UTC)


def _user(storage_limit: int | None) -> User:
    return User(id=1, storage_limit=storage_limit, create_public_collection=False, created=NOW, updated=NOW)


class TestHasStorageFor:
    @pytest.mark.parametrize(
        "storage_limit,used_storage,size,expected",
        [
            (100, 60, 40, True),
            (100, 60, 41, False),
            (None, 10**12, 10**12, True),
        ],
    )
    def test_should_allow_document_up_to_storage_limit_or_without_limit(self, storage_limit, used_storage, size, expected):
        # Act
        has_storage = _user(storage_limit).has_storage_for(used_storage=used_storage, size=size)

        # Assert
        assert has_storage is expected
