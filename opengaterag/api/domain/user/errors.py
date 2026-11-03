from dataclasses import dataclass


@dataclass
class UserNotAuthenticatedError:
    pass


@dataclass
class StorageLimitExceededError:
    pass
