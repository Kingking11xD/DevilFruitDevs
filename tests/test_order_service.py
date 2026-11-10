import json
from pathlib import Path

import pytest
from app.repositories.order_repo import OrderRepo
from app.services.order_service import OrderNotFoundError, OrderService


def make_order(order_id: int, customer_id: int, created_at: str) -> dict:
    """Return a valid order record for tests."""
    return {
        "id": order_id,
        "customer_id": customer_id,
        "restaurant_id": 1,
        "restaurant_name": "Test Restaurant",
        "source_cart_id": order_id,
        "status": "placed",
        "created_at": created_at,
        "delivery_address": "123 Test St",
        "items": [
            {"menu_item_id": 1, "name": "Burger", "unit_price": 1250, "quantity": 2, "line_total": 2500}
        ],
        "subtotal": 2500,
        "total": 2500,
    }


@pytest.fixture
def service(tmp_path: Path) -> OrderService:
    """Create an order service over an isolated shopping file."""
    path = tmp_path / "shopping.json"
    orders = [
        make_order(1, 1, "2026-11-14T18:00:00Z"),
        make_order(2, 2, "2026-11-15T18:00:00Z"),
        make_order(3, 1, "2026-11-16T18:00:00Z"),
    ]
    path.write_text(json.dumps({"carts": [], "orders": orders}), encoding="utf-8")
    return OrderService(OrderRepo(path))


def test_list_for_customer_returns_own_orders_newest_first(service: OrderService) -> None:
    """Test that a customer only sees their own orders, newest first."""
    orders = service.list_for_customer(1)

    assert [order["id"] for order in orders] == [3, 1]


def test_list_for_customer_with_no_orders(service: OrderService) -> None:
    """Test that a customer with no orders gets an empty list."""
    assert service.list_for_customer(99) == []


def test_get_for_customer_returns_own_order(service: OrderService) -> None:
    """Test that a customer can retrieve one of their orders."""
    order = service.get_for_customer(1, 3)

    assert order["id"] == 3
    assert order["customer_id"] == 1


def test_get_for_customer_missing_order(service: OrderService) -> None:
    """Test that a missing order raises a not-found error."""
    with pytest.raises(OrderNotFoundError):
        service.get_for_customer(1, 999)


def test_get_for_customer_other_customers_order(service: OrderService) -> None:
    """Test that another customer's order is treated as not found."""
    with pytest.raises(OrderNotFoundError):
        service.get_for_customer(1, 2)