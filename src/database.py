from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter
from supabase import create_client, Client

from .config import get_settings

T = TypeVar("T", bound=BaseModel)


@lru_cache
def get_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


def select_all(model: type[T]) -> list[T]:
    client = get_client()
    table_name = model.__name__
    response = client.table(table_name).select("*").execute()
    adapter: TypeAdapter[list[T]] = TypeAdapter(list[model])  # type: ignore
    return adapter.validate_python(response.data)


def select_by_id(model: type[T], id_field: str, id_value: str) -> T | None:
    """get single record by ID"""
    client = get_client()
    table_name = model.__name__
    response = client.table(table_name).select("*").eq(id_field, id_value).execute()
    if not response.data:
        return None
    return model.model_validate(response.data[0])


def select_by_field(model: type[T], field: str, value: str) -> list[T]:
    """get all records matching a field value"""
    client = get_client()
    table_name = model.__name__
    response = client.table(table_name).select("*").eq(field, value).execute()
    adapter: TypeAdapter[list[T]] = TypeAdapter(list[model])  # type: ignore
    return adapter.validate_python(response.data)


def upsert_batch(table_name: str, records: list[dict], batch_size: int = 500) -> int:
    """Bulk upsert records more efficient than singular upserts"""
    if not records:
        return 0
    client = get_client()
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        client.table(table_name).upsert(batch).execute()
        total += len(batch)
    return total
