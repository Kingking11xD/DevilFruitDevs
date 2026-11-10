from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class OrderItem(BaseModel):
    """features of one menu item at checkout"""
    menu_item_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    unit_price: int = Field(ge=0)
    quantity: int = Field(gt=0)
    line_total: int = Field(ge=0)

class Order(BaseModel):
    """show saved order created from customer's cart"""
    id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    restaurant_id: int = Field(gt=0)
    restaurant_name: str = Field(min_length=1)
    source_cart_id: int = Field(gt=0)
    status: Literal["placed"]
    created_at: datetime

    # TODO: match the delivery address type keenan uses in accounts
    delivery_address: str = Field(min_length=1, max_length=500)
    items: list[OrderItem] = Field(min_length=1)
    subtotal: int = Field(ge=0)
    total: int = Field(ge=0)