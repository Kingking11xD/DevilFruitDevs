"""test accounts with carts and orders"""

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.api.routes import carts
from app.services import token_service
from main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """temporary data and sessions for each test"""
    (tmp_path / "accounts.json").write_text("[]", encoding="utf-8")
    (tmp_path / "shopping.json").write_text(
        '{"carts": [], "orders": []}', encoding="utf-8")
    (tmp_path / "restaurants.json").write_text(json.dumps([{
        "id": 1,
        "name": "Baratie",
        "cuisine": "Seafood",
        "address": "East Blue",
        "active": True}]), encoding="utf-8")
    (tmp_path / "menu_items.json").write_text(json.dumps([{
        "id": 1,
        "restaurant_id": 1,
        "name": "Burger",
        "price": 1250,
        "available": True,
        "active": True}]), encoding="utf-8")

    # checkout and orders use this folder
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    # these repos already exist so change their paths too
    monkeypatch.setattr(dependencies.repository, "file_path", tmp_path / "accounts.json")
    monkeypatch.setattr(carts.repository, "file_path", tmp_path / "shopping.json")
    monkeypatch.setattr(carts.menu_repository, "file_path", tmp_path / "menu_items.json")
    monkeypatch.setattr(carts.restaurant_repository, "file_path", tmp_path / "restaurants.json")
    monkeypatch.setattr(token_service, "sessions", {})

    with TestClient(app) as test_client:
        yield test_client


def sign_in_new_customer(client: TestClient, email: str = "customer@example.com") -> int:
    """register and log in with an address then return the id"""
    response = client.post("/customers", json={
        "name": "Test Customer",
        "email": email,
        "password": "test-password-123"})
    assert response.status_code == 201
    customer_id = response.json()["id"]

    response = client.post("/auth/login", json={
        "email": email,
        "password": "test-password-123"})
    assert response.status_code == 200
    client.headers["Authorization"] = "Bearer " + response.json()["access_token"]

    response = client.patch("/customers/me/address", json={
        "delivery_address": "123 Test Street"})
    assert response.status_code == 200
    return customer_id


def create_cart_with_items(client: TestClient) -> int:
    """add two burgers and return the cart id"""
    response = client.post("/customers/me/cart")
    assert response.status_code == 201
    cart_id = response.json()["id"]

    response = client.post("/customers/me/cart/items", json={
        "menu_item_id": 1, "quantity": 2})
    assert response.status_code == 200
    return cart_id


def test_customer_can_register_and_place_order(client: TestClient, tmp_path: Path) -> None:
    """new customer can place an order and read it back"""
    customer_id = sign_in_new_customer(client)
    cart_id = create_cart_with_items(client)

    response = client.get("/customers/me/cart")
    assert response.status_code == 200
    total = response.json()["total"]
    assert total == 2500

    response = client.post(f"/carts/{cart_id}/checkout", json={"expected_total": total})
    assert response.status_code == 201
    order = response.json()
    assert order["customer_id"] == customer_id
    assert order["customer_name"] == "Test Customer"
    assert order["delivery_address"] == "123 Test Street"
    assert order["restaurant_id"] == 1
    assert order["restaurant_name"] == "Baratie"
    assert order["source_cart_id"] == cart_id
    assert order["total"] == 2500
    assert order["items"] == [{
        "menu_item_id": 1, "name": "Burger", "unit_price": 1250,
        "quantity": 2, "line_total": 2500}]

    response = client.get(f"/orders/{order['id']}")
    assert response.status_code == 200
    assert response.json() == order

    response = client.get("/orders")
    assert response.status_code == 200
    assert response.json() == [order]

    saved = json.loads((tmp_path / "shopping.json").read_text(encoding="utf-8"))
    assert saved["orders"] == [order]
    assert saved["carts"][0]["id"] == cart_id
    assert saved["carts"][0]["status"] == "closed"


def test_customer_cannot_access_another_customers_cart_or_order(
        client: TestClient, tmp_path: Path) -> None:
    """customers can only use their own carts and orders"""
    sign_in_new_customer(client)
    closed_cart_id = create_cart_with_items(client)
    response = client.post(f"/carts/{closed_cart_id}/checkout", json={"expected_total": 2500})
    assert response.status_code == 201
    order_id = response.json()["id"]
    active_cart_id = create_cart_with_items(client)

    sign_in_new_customer(client, "other@example.com")
    shopping_path = tmp_path / "shopping.json"
    original = shopping_path.read_text(encoding="utf-8")

    assert client.get("/customers/me/cart").status_code == 404
    response = client.post("/customers/me/cart/items", json={
        "menu_item_id": 1, "quantity": 1})
    assert response.status_code == 404
    response = client.patch("/customers/me/cart/items/1", json={"quantity": 5})
    assert response.status_code == 404
    assert client.delete("/customers/me/cart/items/1").status_code == 404
    assert client.delete("/customers/me/cart/items").status_code == 404

    # retries need the ownership check too
    for cart_id in [active_cart_id, closed_cart_id]:
        response = client.post(f"/carts/{cart_id}/checkout", json={"expected_total": 2500})
        assert response.status_code == 404
        assert response.json()["detail"] == "Cart not found"

    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"
    response = client.get("/orders")
    assert response.status_code == 200
    assert response.json() == []
    assert shopping_path.read_text(encoding="utf-8") == original

    second_cart_id = create_cart_with_items(client)
    assert second_cart_id != active_cart_id
    saved = json.loads(shopping_path.read_text(encoding="utf-8"))
    first_customers_data = json.loads(original)
    assert saved["carts"][:2] == first_customers_data["carts"]
    assert saved["orders"] == first_customers_data["orders"]


def test_deactivated_customer_cannot_change_cart_or_checkout(
        client: TestClient, tmp_path: Path) -> None:
    """old token cant change the cart or checkout after deactivation"""
    sign_in_new_customer(client)
    cart_id = create_cart_with_items(client)
    shopping_path = tmp_path / "shopping.json"
    original = shopping_path.read_text(encoding="utf-8")

    response = client.post("/customers/me/deactivate")
    assert response.status_code == 200
    assert response.json()["active"] is False

    # keep the token from before deactivation
    assert client.post("/customers/me/cart").status_code == 403
    assert client.get("/customers/me/cart").status_code == 403
    response = client.post("/customers/me/cart/items", json={
        "menu_item_id": 1, "quantity": 1})
    assert response.status_code == 403
    response = client.patch("/customers/me/cart/items/1", json={"quantity": 5})
    assert response.status_code == 403
    assert client.delete("/customers/me/cart/items/1").status_code == 403
    assert client.delete("/customers/me/cart/items").status_code == 403

    response = client.post(f"/carts/{cart_id}/checkout", json={"expected_total": 2500})
    assert response.status_code == 403
    assert response.json()["detail"] == "Account is inactive"
    assert shopping_path.read_text(encoding="utf-8") == original


def test_account_changes_preserve_saved_orders(client: TestClient, tmp_path: Path) -> None:
    """profile edits and deactivation leave saved orders alone"""
    sign_in_new_customer(client)
    cart_id = create_cart_with_items(client)
    response = client.post(f"/carts/{cart_id}/checkout", json={"expected_total": 2500})
    assert response.status_code == 201
    order = response.json()
    assert order["customer_name"] == "Test Customer"
    assert order["delivery_address"] == "123 Test Street"

    shopping_path = tmp_path / "shopping.json"
    original = shopping_path.read_text(encoding="utf-8")

    response = client.patch("/customers/me", json={"name": "Changed Name"})
    assert response.status_code == 200
    response = client.patch("/customers/me/address", json={
        "delivery_address": "456 New Street"})
    assert response.status_code == 200
    response = client.get("/customers/me")
    assert response.status_code == 200
    assert response.json()["name"] == "Changed Name"
    assert response.json()["delivery_address"] == "456 New Street"

    response = client.get(f"/orders/{order['id']}")
    assert response.status_code == 200
    assert response.json() == order
    assert shopping_path.read_text(encoding="utf-8") == original

    response = client.post("/customers/me/deactivate")
    assert response.status_code == 200
    assert response.json()["active"] is False

    # saved orders stay even though the old token cant read them
    assert client.get(f"/orders/{order['id']}").status_code == 403
    assert client.get("/orders").status_code == 403
    response = client.post(f"/carts/{cart_id}/checkout", json={"expected_total": 2500})
    assert response.status_code == 403
    assert response.json()["detail"] == "Account is inactive"
    assert shopping_path.read_text(encoding="utf-8") == original
    saved = json.loads(shopping_path.read_text(encoding="utf-8"))
    assert saved["orders"] == [order]
