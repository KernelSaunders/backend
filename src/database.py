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

def insert_one(table_name: str, record: dict) -> dict:
    """Insert a single record, return the inserted row."""
    client = get_client()
    response = client.table(table_name).insert(record).execute()
    return response.data[0]


def update_by_id(table_name: str, id_field: str, id_value: str, updates: dict) -> dict:
    """Update a record by its ID field, return the updated row."""
    client = get_client()
    response = client.table(table_name).update(updates).eq(id_field, id_value).execute()
    if not response.data:
        return {}
    return response.data[0]


def log_entity_change(entity_type: str, entity_id: str, changed_by: str, change_summary: dict) -> None:
    """Generic change logger — writes to the ChangeLog table."""
    client = get_client()
    client.table("ChangeLog").insert(
        {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "changed_by": changed_by,
            "change_summary": change_summary,
        }
    ).execute()


# Function to record a verification change to a claim
def log_claim_change(
    claim_id: str,
    changed_by: str,
    action: str,
    old_confidence: str | None = None,
    new_confidence: str | None = None,
    notes: str | None = None,
    old_verified: bool | None = None,
    new_verified: bool | None = None,
):
    # Our jsonb way of storing what we have changed in a readable format
    summary = {
        "action": action
    }
    
    if old_confidence or new_confidence:
        summary["old_confidence"] = old_confidence
        summary["new_confidence"] = new_confidence
    if notes:
        summary["notes"] = notes 
    if old_verified is not None: #i.e Had some verified status before
        summary["old_verified_status"] = old_verified
        summary["new_verified_status"] = new_verified
        
    # Creates connection with db and updates ChangeLog
    client = get_client()
    client.table("ChangeLog").insert({
        "entity_type": "Claim",
        "entity_id": claim_id,
        "changed_by": changed_by,
        "change_summary": summary,
    }).execute()