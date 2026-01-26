import os
from functools import lru_cache
from typing import TypeVar, cast

from dotenv import load_dotenv
from pydantic import BaseModel, TypeAdapter
from supabase import create_client, Client

from models import Product, Stage, InputShare

load_dotenv()

# lru_cache as we only create one instance of the client
@lru_cache
def get_client() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    return create_client(url, key)


# T is a type placeholder - bound=BaseModel means T must be a Pydantic model
T = TypeVar("T", bound=BaseModel)


# Pass a class, get a typed list back
# eg select_all(Product) -> list[Product]
def select_all(model: type[T]) -> list[T]:
    client = get_client()
    table_name = model.__name__
    response = client.table(table_name).select("*").execute()
    return TypeAdapter(list[model]).validate_python(response.data)


if __name__ == "__main__":
    products: list[Product] = select_all(Product)
    stages: list[Stage] = select_all(Stage)
    input_shares: list[InputShare] = select_all(InputShare)

    
    print("Products:")
    for product in products:
        print(f"  {product.name} ({product.brand})")

    print("\nStages:")
    for stage in stages:
        print(f"  {stage.stage_type} - {stage.location_country}")

    print("\nInput Shares:")
    for share in input_shares:
        print(f"  {share.input_name}: {share.percentage}%")
