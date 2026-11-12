from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class OrderItem(BaseModel):
    """features of one menu item at checkout"""
    menu_item_id: int = Field(gt=0)
    name: str = Field(min_length=1)
    unit_price: int = Field(ge=0)
    quantity: int = Field(gt=0)
    line_total: int = Field(ge=0)


    @model_validator(mode="after")
    def check_line_total(self) -> "OrderItem":
        """Reject an item whose line total is not unit price times quantity."""
        if self.line_total != self.unit_price * self.quantity:
            raise ValueError("line_total must equal unit_price * quantity")
        return self

class Order(BaseModel):
    """show saved order created from customer's cart"""
    id: int = Field(gt=0)
    customer_id: int = Field(gt=0)
    customer_name: str = Field(min_length=1, max_length=100)
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

    
    @model_validator(mode="after")
    def check_subtotal(self) -> "Order":
        """Reject an order whose subtotal is not the sum of its line totals."""
        if self.subtotal != sum(item.line_total for item in self.items):
            raise ValueError("subtotal must equal the sum of item line totals")
        return self