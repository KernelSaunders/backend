from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class Product(BaseModel):
    product_id: str
    name: str
    category: Literal["food", "luxury", "supplements", "other"]
    brand: str | None = None
    description: str | None = None
    image: str | None = None
    created_at: datetime
    updated_at: datetime


class Stage(BaseModel):
    stage_id: str
    product_id: str | None = None
    stage_type: str
    location_country: str | None = None
    location_region: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None
    sequence_order: int | None = None
    created_at: datetime | None = None


class InputShare(BaseModel):
    input_id: str
    product_id: str | None = None
    input_name: str
    country: str
    percentage: Decimal | None = None
    notes: str | None = None
    created_at: datetime

