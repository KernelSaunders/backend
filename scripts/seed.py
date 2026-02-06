import json
import sys
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import get_client
from src.models import (
    Product,
    Stage,
    InputShare,
    Claim,
    Evidence,
    IssueReport,
    ChangeLog,
)

T = TypeVar("T", bound=BaseModel)

SEEDING_DIR = Path(__file__).parent / "seeding"
BASE_TIMESTAMP = "2025-01-01T12:00:00"

TABLES: list[tuple[type[BaseModel], str, list[str]]] = [
    (Product, "products.json", ["created_at", "updated_at"]),
    (Stage, "stages.json", ["created_at"]),
    (InputShare, "input_shares.json", ["created_at"]),
    (Claim, "claims.json", ["created_at", "updated_at"]),
    (Evidence, "evidence.json", ["created_at"]),
    (IssueReport, "issues.json", ["created_at", "updated_at"]),
    (ChangeLog, "change_logs.json", ["timestamp"]),
]


def load_fixture(filename: str) -> list[dict]:
    filepath = SEEDING_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def add_timestamps(records: list[dict], fields: list[str]) -> list[dict]:
    for record in records:
        for field in fields:
            if field not in record or record[field] is None:
                record[field] = BASE_TIMESTAMP
    return records


def validate_records(model: type[T], records: list[dict]) -> list[T]:
    validated = []
    for i, record in enumerate(records):
        try:
            validated.append(model.model_validate(record))
        except ValidationError as e:
            raise ValueError(f"failed validation {e}") from e
    return validated


def seed_database():
    client = get_client()

    try:
        for model, fixture_file, timestamp_fields in TABLES:
            table_name = model.__name__
            records = load_fixture(fixture_file)
            if not records:
                print(f"  {table_name} nothing in")
                continue

            records = add_timestamps(records, timestamp_fields)
            validated = validate_records(model, records)
            data = [r.model_dump(mode="json") for r in validated]

            client.table(table_name).upsert(data).execute()
            print(f"  {table_name} {len(data)} records upserted woof")

    except Exception as e:
        print(f"seeding failed: {e}")
    
if __name__ == "__main__":
    seed_database()
