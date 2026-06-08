from uuid import UUID


def ensure_uuid(value) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))