import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_customer
from app.api.routes.orders import get_order_service, router
from app.repositories.order_repo import OrderRepo
from app.services.order_service import OrderService


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


CUSTOMER = {"id": 1, "name": "Ana", "role": "customer", "active": True}


@pytest.fixture
def app(tmp_path: Path) -> Iterator[FastAPI]:
    """Create an app with the order routes using an isolated shopping file."""
    path = tmp_path / "shopping.json"
    orders = [
        make_order(1, 1, "2026-11-14T18:00:00Z"),
        make_order(2, 2, "2026-11-15T18:00:00Z"),
        make_order(3, 1, "2026-11-16T18:00:00Z"),
    ]
    path.write_text(json.dumps({"carts": [], "orders": orders}), encoding="utf-8")

    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_order_service] = lambda: OrderService(OrderRepo(path))
    yield test_app
    test_app.dependency_overrides.clear()


@pytest.fixture
def signed_in(app: FastAPI) -> TestClient:
    """Return a client signed in as customer 1."""
    app.dependency_overrides[get_current_customer] = lambda: CUSTOMER
    return TestClient(app)


def test_list_my_orders(signed_in: TestClient) -> None:
    """Test that a customer gets their own orders, newest first."""
    response = signed_in.get("/customers/me/orders")

    assert response.status_code == 200
    assert [order["id"] for order in response.json()] == [3, 1]


def test_list_my_orders_empty(app: FastAPI) -> None:
    """Test that a customer with no orders gets an empty list."""
    app.dependency_overrides[get_current_customer] = lambda: {**CUSTOMER, "id": 99}

    response = TestClient(app).get("/customers/me/orders")

    assert response.status_code == 200
    assert response.json() == []


def test_get_my_order(signed_in: TestClient) -> None:
    """Test that a customer can view one of their orders with its saved details."""
    response = signed_in.get("/customers/me/orders/3")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == 3
    assert body["delivery_address"] == "123 Test St"
    assert body["items"][0]["unit_price"] == 1250


def test_get_my_order_not_found(signed_in: TestClient) -> None:
    """Test that a missing order returns 404."""
    response = signed_in.get("/customers/me/orders/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_get_other_customers_order(signed_in: TestClient) -> None:
    """Test that another customer's order returns 404 without revealing it exists."""
    response = signed_in.get("/customers/me/orders/2")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


@pytest.mark.parametrize("url", ["/customers/me/orders", "/customers/me/orders/1"])
def test_orders_require_authentication(app: FastAPI, url: str) -> None:
    """Test that requests without a token are rejected with 401."""
    response = TestClient(app).get(url)

    assert response.status_code == 401


def test_orders_storage_error(app: FastAPI, tmp_path: Path) -> None:
    """Test that a broken shopping file returns 500 instead of crashing."""
    broken = tmp_path / "broken.json"
    broken.write_text("[]", encoding="utf-8")
    app.dependency_overrides[get_current_customer] = lambda: CUSTOMER
    app.dependency_overrides[get_order_service] = lambda: OrderService(OrderRepo(broken))

    response = TestClient(app).get("/customers/me/orders")

    assert response.status_code == 500
    assert response.json()["detail"] == "Orders could not be loaded"