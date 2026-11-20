"""End-to-end test of the customer-to-order workflow through the real API.
Customer -> Restaurant -> Menu -> Cart -> Checkout -> Order, focusing on order testing
Uses isolated data files, so the committed data in data/ is never changed.
"""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.api.routes import carts, menu
from app.services import token_service
from main import app


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point every repository at a temporary data folder with one restaurant and menu."""
    (tmp_path / "accounts.json").write_text("[]")
    (tmp_path / "shopping.json").write_text('{"carts": [], "orders": []}')
    (tmp_path / "restaurants.json").write_text(json.dumps([
        {"id": 1, "name": "Baratie", "cuisine": "Seafood", "address": "East Blue"},
    ]))
    (tmp_path / "menu_items.json").write_text(json.dumps([
        {"id": 1, "restaurant_id": 1, "name": "Burger", "price": 1250, "available": True, "active": True},
        {"id": 2, "restaurant_id": 1, "name": "Fries", "price": 400, "available": True, "active": True},
    ]))

    monkeypatch.setattr(dependencies.repository, "file_path", tmp_path / "accounts.json")
    monkeypatch.setattr(carts.repository, "file_path", tmp_path / "shopping.json")
    monkeypatch.setattr(carts.menu_repository, "file_path", tmp_path / "menu_items.json")
    monkeypatch.setattr(menu.menu_repository, "file_path", tmp_path / "menu_items.json")
    monkeypatch.setattr(menu.restaurant_repository, "file_path", tmp_path / "restaurants.json")
    monkeypatch.setattr(token_service, "sessions", {})
    monkeypatch.setenv("DATA_DIR", str(tmp_path))  # Checkout and order services read this
    return tmp_path


def test_customer_to_order_workflow(data_dir: Path) -> None:
    """A new customer can browse, build a cart, check out once and view the saved order."""
    client = TestClient(app)

    # Customer: register, sign in and set a delivery address
    assert client.post("/customers", json={
        "name": "Ana Lopez", "email": "ana@example.com", "password": "Password123!",
    }).status_code == 201
    login = client.post("/auth/login", json={"email": "ana@example.com", "password": "Password123!"})
    assert login.status_code == 200
    client.headers["Authorization"] = f"Bearer {login.json()['access_token']}"
    assert client.patch("/customers/me/address", json={"delivery_address": "123 Test St"}).status_code == 200

    # Restaurant and menu: browse the menu
    menu_items = client.get("/restaurants/1/menu-items")
    assert menu_items.status_code == 200
    assert {item["id"] for item in menu_items.json()} == {1, 2}

    # Cart: build it and read the backend-calculated total
    cart = client.post("/customers/me/cart")
    assert cart.status_code == 201
    cart_id = cart.json()["id"]
    assert client.post("/customers/me/cart/items", json={"menu_item_id": 1, "quantity": 2}).status_code == 200
    assert client.post("/customers/me/cart/items", json={"menu_item_id": 2, "quantity": 1}).status_code == 200
    total = client.get("/customers/me/cart").json()["total"]
    assert total == 2900  # 2 x 1250 + 1 x 400

    # Checkout: the order keeps a snapshot of what was bought
    checkout = client.post(f"/carts/{cart_id}/checkout", json={"expected_total": total})
    assert checkout.status_code == 201
    order = checkout.json()
    assert order["total"] == total
    assert order["customer_name"] == "Ana Lopez"
    assert order["restaurant_name"] == "Baratie"
    assert order["delivery_address"] == "123 Test St"
    assert [item["line_total"] for item in order["items"]] == [2500, 400]

    # Retrying the same checkout returns the same order instead of a duplicate
    retry = client.post(f"/carts/{cart_id}/checkout", json={"expected_total": total})
    assert retry.status_code == 200
    assert retry.json() == order

    # Order: the cart is closed and the order can be viewed
    assert client.get("/customers/me/cart").status_code == 404
    assert client.get("/orders").json() == [order]
    assert client.get(f"/orders/{order['id']}").json() == order

    # Persistence: one order and the closed cart are saved to disk
    shopping = json.loads((data_dir / "shopping.json").read_text())
    assert shopping["orders"] == [order]
    assert shopping["carts"][0]["status"] == "closed"