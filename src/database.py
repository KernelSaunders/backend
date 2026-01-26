import os
from functools import lru_cache
from typing import TypeVar

from dotenv import load_dotenv
from pydantic import BaseModel, TypeAdapter
from supabase import create_client, Client

load_dotenv()

T = TypeVar("T", bound=BaseModel)


@lru_cache
def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    return create_client(url, key)


def select_all(model: type[T]) -> list[T]:
    client = get_client()
    table_name = model.__name__
    response = client.table(table_name).select("*").execute()
    return TypeAdapter(list[model]).validate_python(response.data)
