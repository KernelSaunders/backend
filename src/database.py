from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter
from supabase import create_client, Client

from src.config import get_settings

T = TypeVar("T", bound=BaseModel)


@lru_cache
def get_client() -> Client:
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)


def select_all(model: type[T]) -> list[T]:
    client = get_client()
    table_name = model.__name__
    response = client.table(table_name).select("*").execute()
    return TypeAdapter(list[model]).validate_python(response.data)
