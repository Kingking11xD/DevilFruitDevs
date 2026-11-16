"""Integration tests for shopping carts across subsystems"""


import json

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from main import app
from app.api import dependencies
from app.api.routes import carts, menu
from app.services import token_service


@pytest.fixture
def integration_setup(tmp_path, monkeypatch):
    """Set up shared test data for cart and menu integration."""
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text("[]")

    shopping_path = tmp_path / "shopping.json"
    shopping_path.write_text('{"carts": [], "orders": []}')

    restaurants_path = tmp_path / "restaurants.json"
    restaurants_path.write_text(json.dumps([
        {
            "id": 1,
            "name": "Burger House",
            "cuisine": "American",
            "address": "1 Test Street",
        },
        {
            "id": 2,
            "name": "Pizza House",
            "cuisine": "Italian",
            "address": "2 Test Street",
        },
    ]))

    menu_path = tmp_path / "menu_items.json"
    menu_path.write_text(json.dumps([
        {
            "id": 1,
            "restaurant_id": 1,
            "name": "Burger",
            "price": 100,
            "available": True,
            "active": True,
        },
        {
            "id": 2,
            "restaurant_id": 2,
            "name": "Pizza",
            "price": 150,
            "available": True,
            "active": True,
        },
        {
            "id": 3,
            "restaurant_id": 1,
            "name": "Fries",
            "price": 50,
            "available": False,
            "active": True,
        },
    ]))

    monkeypatch.setattr(
        dependencies.repository, "file_path", accounts_path
    )
    monkeypatch.setattr(
        carts.repository, "file_path", shopping_path
    )
    monkeypatch.setattr(
        carts.menu_repository, "file_path", menu_path
    )
    monkeypatch.setattr(
        menu.menu_repository, "file_path", menu_path
    )
    monkeypatch.setattr(
        menu.restaurant_repository, "file_path", restaurants_path
    )
    monkeypatch.setattr(token_service, "sessions", {})
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    client = TestClient(app)

    created = client.post(
        "/customers",
        json={
            "name": "Test Customer",
            "email": "cart@example.com",
            "password": "Password123!",
        },
    )
    assert created.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "cart@example.com",
            "password": "Password123!",
        },
    )
    assert login.status_code == 200

    client.headers["Authorization"] = (
        f"Bearer {login.json()['access_token']}"
    )

    manager = dependencies.repository.create_staff(
        "Manager", "manager@test.com", "unused-hash",
        "restaurant_user", [1],
    )
    manager_headers = {
        "Authorization": (
            f"Bearer {token_service.create_access_token(manager['id'])}"
        )
    }

    return {
        "client": client,
        "manager_headers": manager_headers,
        "shopping_path": shopping_path,
        "menu_path": menu_path,
        "restaurants_path": restaurants_path,
    }


def test_menu_deactivation_blocks_cart_add(integration_setup):
    """Test that deactivating a menu item blocks cart additions."""
    client: TestClient = integration_setup["client"]
    manager_headers: dict[str, str] = integration_setup["manager_headers"]
    shopping_path: Path = integration_setup["shopping_path"]

    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    updated = client.patch(
        "/restaurants/1/menu-items/1",
        json={"active": False},
        headers=manager_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["active"] is False

    shopping_before = shopping_path.read_bytes()

    rejected = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 1},
    )
    assert rejected.status_code == 409

    assert shopping_path.read_bytes() == shopping_before

    response = client.get("/customers/me/cart")
    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 2
    assert "inactive" in response.json()["items"][0]["problems"]

    address = client.patch(
        "/customers/me/address",
        json={"delivery_address": "123 Test Street"},
    )
    assert address.status_code == 200

    shopping_before_checkout = shopping_path.read_bytes()

    checkout = client.post(
        f"/carts/{created.json()['id']}/checkout",
        json={"expected_total": response.json()["total"]},
    )
    assert checkout.status_code == 409
    assert checkout.json()["detail"] == (
        "Some items are no longer available"
    )

    assert shopping_path.read_bytes() == shopping_before_checkout

    saved_data = json.loads(shopping_path.read_text())
    assert saved_data["orders"] == []
    assert saved_data["carts"][0]["status"] == "active"


def test_menu_unavailability_blocks_cart_add(integration_setup):
    """Test that unavailable menu items are flagged and can't be added."""
    client: TestClient = integration_setup["client"]
    manager_headers: dict[str, str] = integration_setup["manager_headers"]
    shopping_path: Path = integration_setup["shopping_path"]

    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    updated = client.patch(
        "/restaurants/1/menu-items/1",
        json={"available": False},
        headers=manager_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["available"] is False
    assert updated.json()["active"] is True

    response = client.get("/customers/me/cart")
    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 2
    assert "unavailable" in response.json()["items"][0]["problems"]

    shopping_before = shopping_path.read_bytes()

    rejected = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 1},
    )
    assert rejected.status_code == 409
    assert shopping_path.read_bytes() == shopping_before

    address = client.patch(
        "/customers/me/address",
        json={"delivery_address": "123 Test Street"},
    )
    assert address.status_code == 200

    shopping_before_checkout = shopping_path.read_bytes()

    checkout = client.post(
        f"/carts/{created.json()['id']}/checkout",
        json={"expected_total": response.json()["total"]},
    )
    assert checkout.status_code == 409
    assert checkout.json()["detail"] == (
        "Some items are no longer available"
    )

    assert shopping_path.read_bytes() == shopping_before_checkout

    saved_data = json.loads(shopping_path.read_text())
    assert saved_data["orders"] == []
    assert saved_data["carts"][0]["status"] == "active"


def test_deactivated_customer_cannot_modify_cart(integration_setup):
    """Test that deactivated customers can't modify stored carts."""
    client: TestClient = integration_setup["client"]
    shopping_path: Path = integration_setup["shopping_path"]

    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    deactivated = client.post("/customers/me/deactivate")
    assert deactivated.status_code == 200
    assert deactivated.json()["active"] is False

    shopping_before = shopping_path.read_bytes()

    rejected_create = client.post("/customers/me/cart")
    assert rejected_create.status_code == 403
    assert rejected_create.json()["detail"] == "Account is inactive"

    rejected_add = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 1},
    )
    assert rejected_add.status_code == 403
    assert rejected_add.json()["detail"] == "Account is inactive"

    assert shopping_path.read_bytes() == shopping_before

    saved_data = json.loads(shopping_path.read_text())
    assert len(saved_data["carts"]) == 1
    assert saved_data["carts"][0]["items"] == [
        {"menu_item_id": 1, "quantity": 2}
    ]


def test_add_item_from_missing_restaurant(integration_setup):
    """Test that items from nonexistent restaurants can't be added."""
    client: TestClient = integration_setup["client"]
    menu_path: Path = integration_setup["menu_path"]
    shopping_path: Path = integration_setup["shopping_path"]

    menu_items = json.loads(menu_path.read_text())
    menu_items.append({
        "id": 4,
        "restaurant_id": 999,
        "name": "Invalid Sushi",
        "price": 100,
        "available": True,
        "active": True,
    })
    menu_path.write_text(json.dumps(menu_items))

    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    shopping_before = shopping_path.read_bytes()

    response = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 4, "quantity": 1},
    )
    assert response.status_code == 404
    assert shopping_path.read_bytes() == shopping_before


def test_new_cart_after_checkout(integration_setup):
    """Test that a new cart can use a different restaurant after checkout."""
    client: TestClient = integration_setup["client"]

    address = client.patch(
        "/customers/me/address",
        json={"delivery_address": "123 Test Street"},
    )
    assert address.status_code == 200

    created = client.post("/customers/me/cart")
    assert created.status_code == 201
    old_cart_id = created.json()["id"]

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    details = client.get("/customers/me/cart")
    assert details.status_code == 200
    
    checkout = client.post(
        f"/carts/{old_cart_id}/checkout",
        json={"expected_total": details.json()["total"]},
    )
    assert checkout.status_code == 201

    response = client.get("/customers/me/cart")
    assert response.status_code == 404

    new_cart = client.post("/customers/me/cart")
    assert new_cart.status_code == 201

    cart = new_cart.json()
    assert cart["id"] != old_cart_id
    assert cart["status"] == "active"
    assert cart["restaurant_id"] is None
    assert cart["items"] == []

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 2, "quantity": 1},
    )
    assert added.status_code == 200

    details = client.get("/customers/me/cart")
    assert details.status_code == 200
    assert details.json()["id"] == cart["id"]
    assert details.json()["restaurant_id"] == 2
    assert details.json()["items"][0]["menu_item_id"] == 2


def test_menu_price_change_during_checkout(integration_setup):
    """Test that checkout rejects an outdated cart total."""
    client: TestClient = integration_setup["client"]
    manager_headers: dict[str, str] = integration_setup["manager_headers"]
    shopping_path: Path = integration_setup["shopping_path"]

    address = client.patch(
        "/customers/me/address",
        json={"delivery_address": "123 Test Street"},
    )
    assert address.status_code == 200

    created = client.post("/customers/me/cart")
    assert created.status_code == 201
    cart_id = created.json()["id"]

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    details = client.get("/customers/me/cart")
    assert details.status_code == 200
    old_total = details.json()["total"]
    assert old_total == 200

    updated = client.patch(
        "/restaurants/1/menu-items/1",
        json={"price": 125},
        headers=manager_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["price"] == 125

    shopping_before = shopping_path.read_bytes()

    rejected = client.post(
        f"/carts/{cart_id}/checkout",
        json={"expected_total": old_total},
    )
    assert rejected.status_code == 409
    assert rejected.json()["detail"] == {
        "message": "Order total has changed",
        "total": 250,
    }

    assert shopping_path.read_bytes() == shopping_before

    details = client.get("/customers/me/cart")
    assert details.status_code == 200
    assert details.json()["total"] == 250

    checkout = client.post(
        f"/carts/{cart_id}/checkout",
        json={"expected_total": 250},
    )
    assert checkout.status_code == 201

    order = checkout.json()
    assert order["items"][0]["unit_price"] == 125
    assert order["items"][0]["line_total"] == 250

    saved_data = json.loads(shopping_path.read_text())
    assert len(saved_data["orders"]) == 1
    assert saved_data["carts"][0]["status"] == "closed"
