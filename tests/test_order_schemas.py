import pytest
from pydantic import ValidationError
from app.schemas.order import Order, OrderItem

def valid_order_data() -> dict:
    """Return valid order data for tests."""
    return {
        "id": 1,
        "customer_id": 2,
        "customer_name": "Ana Lopez",
        "restaurant_id": 3,
        "restaurant_name": "Test Restaurant",
        "source_cart_id": 4,
        "status": "placed",
        "created_at": "2026-11-15T18:00:00Z",
        "delivery_address": "123 Test St",
        "items": [
            {
                "menu_item_id": 5,
                "name": "Burger",
                "unit_price": 1250,
                "quantity": 2,
                "line_total": 2500,
            }
        ],
        "subtotal": 2500,
        "total": 2500,
    }

def test_order_model_valid() -> None:
    """Test that a valid order is accepted."""
    order = Order(**valid_order_data())

    assert order.id == 1
    assert order.customer_name == "Ana Lopez"
    assert order.status == "placed"
    assert order.items[0].line_total == 2500
    assert order.total == 2500


@pytest.mark.parametrize(
    "field, value",
    [
        ("status", "delivered"),
        ("items", []),
        ("total", -1),
        ("source_cart_id", 0),
        ("customer_name", ""),
        ("customer_name", "a" * 101),
        ("restaurant_name", ""),
        ("delivery_address", ""),
        ("delivery_address", "a" * 501),
    ],
)
def test_order_model_invalid(field: str, value) -> None:
    """Test that invalid order data is rejected."""
    data = valid_order_data()
    data[field] = value

    with pytest.raises(ValidationError):
        Order(**data)

def test_order_model_rejects_wrong_subtotal() -> None:
    """Test that an order whose subtotal doesn't match its items is rejected."""
    data = valid_order_data()
    data["subtotal"] = 2000
 
    with pytest.raises(ValidationError):
        Order(**data)
 
def test_order_item_rejects_wrong_line_total() -> None:
    """Test that an item whose line total isn't price times quantity is rejected."""
    data = valid_order_data()["items"][0]
    data["line_total"] = 1250
 
    with pytest.raises(ValidationError):
        OrderItem(**data)
 

@pytest.mark.parametrize(
    "field, value",
    [
        ("quantity", 0),
        ("unit_price", -1),
        ("menu_item_id", 0),
        ("name", ""),
    ],
)
def test_order_item_invalid(field: str, value) -> None:
    """Test that invalid order item snapshots are rejected."""
    data = valid_order_data()["items"][0]
    data[field] = value

    with pytest.raises(ValidationError):
        OrderItem(**data)