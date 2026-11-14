import pytest
from pydantic import ValidationError

from app.schemas.cart import Cart, CartItem, CartItemAdd, CartItemUpdate
from app.schemas.menu import MenuItemCreate, MenuItemUpdate

@pytest.mark.parametrize(
    "data",
    [
        {"menu_item_id": 1, "quantity": 0},
        {"menu_item_id": 1, "quantity": -1},
        {"menu_item_id": 1, "quantity": True},
        {"menu_item_id": 1, "quantity": "2"},
        {"menu_item_id": 0, "quantity": 2},
        {"menu_item_id": True, "quantity": 2},
        {"menu_item_id": 1, "quantity": 2, "price": 100},
    ],
)
def test_cart_item_add_invalid_data(data: dict) -> None:
    """Test that invalid cart item inputs are rejected."""
    with pytest.raises(ValidationError):
        CartItemAdd(**data)

@pytest.mark.parametrize(
    "data",
    [
        {},
        {"quantity": 0},
        {"quantity": -1},
        {"quantity": True},
        {"quantity": "2"},
        {"quantity": None},
        {"quantity": 2, "menu_item_id": 1},
    ],
)
def test_cart_item_update_invalid_data(data: dict) -> None:
    """Test that invalid cart item quantity updates are rejected."""
    with pytest.raises(ValidationError):
        CartItemUpdate(**data)

def test_cart_model() -> None:
    """Test that a cart accepts valid data and rejects invalid statuses."""
    cart = Cart(
        id=1,
        customer_id=2,
        restaurant_id=3,
        status="active",
        items=[CartItem(menu_item_id=5, quantity=2)],
    )

    assert cart.id == 1
    assert cart.customer_id == 2
    assert cart.restaurant_id == 3
    assert cart.status == "active"
    assert cart.items[0].menu_item_id == 5
    assert cart.items[0].quantity == 2

    with pytest.raises(ValidationError):
        Cart(
            id=1,
            customer_id=2,
            restaurant_id=None,
            status="pending",
            items=[],
        )


@pytest.mark.parametrize("value", ["yes", 1, 0, None])
def test_menu_item_create_invalid_availability(value):
    """Test that creating menu items rejects invalid availability values."""
    with pytest.raises(ValidationError):
        MenuItemCreate(name="Pizza", price=100, available=value)


@pytest.mark.parametrize("field", ["available", "active"])
@pytest.mark.parametrize("value", ["yes", 1, 0, None])
def test_menu_item_update_invalid_status(field, value):
    """Test that menu item status updates reject invalid values."""
    with pytest.raises(ValidationError):
        MenuItemUpdate(**{field: value})
