import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_current_customer
from app.api.routes.checkout import get_checkout_service, router
from app.services.checkout_service import CheckoutService

CUSTOMER = {"id": 1, "name": "Ana Lopez", "role": "customer", "active": True}


def write_json(path: Path, data) -> None:
    """Write JSON test data to a file."""
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def files(tmp_path: Path) -> dict[str, Path]:
    """Create isolated data files with one active cart."""
    paths = {
        "shopping": tmp_path / "shopping.json",
        "accounts": tmp_path / "accounts.json",
        "restaurants": tmp_path / "restaurants.json",
        "menu_items": tmp_path / "menu_items.json",
    }
    write_json(paths["accounts"], [{**CUSTOMER, "delivery_address": "123 Test St"}])
    write_json(paths["restaurants"], [{"id": 1, "name": "Baratie", "cuisine": "Seafood", "address": "East Blue"}])
    write_json(paths["menu_items"], [
        {"id": 1, "restaurant_id": 1, "name": "Burger", "price": 1250, "available": True},
    ])
    write_json(paths["shopping"], {
        "carts": [{"id": 5, "customer_id": 1, "restaurant_id": 1, "status": "active",
                   "items": [{"menu_item_id": 1, "quantity": 2}]}],
        "orders": [],
    })
    return paths


@pytest.fixture
def app(files: dict[str, Path]) -> Iterator[FastAPI]:
    """Create an app with the checkout route using the isolated files."""
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_checkout_service] = lambda: CheckoutService(
        shopping_path=files["shopping"],
        accounts_path=files["accounts"],
        restaurants_path=files["restaurants"],
        menu_items_path=files["menu_items"],
        clock=lambda: "2026-11-15T18:00:00Z",
    )
    yield test_app
    test_app.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Return a client signed in as customer 1."""
    app.dependency_overrides[get_current_customer] = lambda: CUSTOMER
    return TestClient(app)


def change_shopping(files: dict[str, Path], change) -> None:
    """Change the isolated shopping file."""
    data = json.loads(files["shopping"].read_text(encoding="utf-8"))
    change(data)
    write_json(files["shopping"], data)


def test_checkout_success(client: TestClient, files: dict[str, Path]) -> None:
    """Test that checkout returns 201 with the created order."""
    response = client.post("/customers/me/checkout")

    assert response.status_code == 201
    body = response.json()
    assert body["source_cart_id"] == 5
    assert body["customer_name"] == "Ana Lopez"
    assert body["total"] == 2500


def test_checkout_no_active_cart(client: TestClient, files: dict[str, Path]) -> None:
    """Test that checking out twice returns 404 the second time because the cart is closed."""
    client.post("/customers/me/checkout")

    response = client.post("/customers/me/checkout")

    assert response.status_code == 404
    assert response.json()["detail"] == "No active cart"


def test_checkout_empty_cart(client: TestClient, files: dict[str, Path]) -> None:
    """Test that an empty cart returns 400."""
    change_shopping(files, lambda shopping: shopping["carts"][0].update(items=[]))

    response = client.post("/customers/me/checkout")

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart is empty"


def test_checkout_unavailable_item(client: TestClient, files: dict[str, Path]) -> None:
    """Test that an item that became unavailable returns 409."""
    write_json(files["menu_items"], [
        {"id": 1, "restaurant_id": 1, "name": "Burger", "price": 1250, "available": False},
    ])

    response = client.post("/customers/me/checkout")

    assert response.status_code == 409


def test_checkout_requires_authentication(app: FastAPI) -> None:
    """Test that checkout without a token returns 401."""
    response = TestClient(app).post("/customers/me/checkout")

    assert response.status_code == 401