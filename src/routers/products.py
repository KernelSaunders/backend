from fastapi import APIRouter

from ..models import Product
from ..database import select_all

router = APIRouter(prefix="/products", tags=["products"])


@router.get("")
def get_products() -> list[Product]:
    return select_all(Product)
