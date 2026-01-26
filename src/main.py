from fastapi import FastAPI

from src.models import Product
from src.database import select_all

app = FastAPI()


@app.get("/products")
def get_products() -> list[Product]:
    return select_all(Product)
