from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

class CartItem(BaseModel):
    """Represent a menu item and its quantity in a shopping cart."""
    menu_item_id: int
    quantity: int = Field(strict=True, gt=0)

class Cart(BaseModel):
    """Represent a shopping cart belonging to a customer."""
    id: int
    customer_id: int
    restaurant_id: int | None
    status: Literal["active", "closed"]
    items: list[CartItem]

class CartItemAdd(BaseModel):
    """Validate the data required to add an item to a cart."""
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    menu_item_id: int = Field(strict=True, gt=0)
    quantity: int = Field(strict=True, gt=0)

class CartItemUpdate(BaseModel):
    """Validate the quantity when updating an existing cart item."""
    model_config = ConfigDict(
        extra="forbid",
    )

    quantity: int = Field(strict=True, gt=0)