"""Tests for shopping cart API routes"""

import pytest
import json
from fastapi.testclient import TestClient

from main import app
from app.api import dependencies
from app.api.routes import carts
from app.services import token_service
from app.repositories.cart_repo import CartRepo

@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create an authenticated customer with temporary storage."""
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text("[]")

    shopping_path = tmp_path / "shopping.json"
    shopping_path.write_text('{"carts": [], "orders": []}')

    menu_file = tmp_path / "menu_items.json"
    menu_file.write_text(
        json.dumps([
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
        ])
    )

    monkeypatch.setattr(
        dependencies.repository, "file_path", accounts_path
    )
    monkeypatch.setattr(
        carts.repository, "file_path", shopping_path
    )
    monkeypatch.setattr(token_service, "sessions", {})
    monkeypatch.setattr(carts.menu_repository, "file_path", menu_file)

    client = TestClient(app)

    client.post(
        "/customers",
        json={
            "name": "Test Customer",
            "email": "cart@example.com",
            "password": "Password123!",
        },
    )

    login = client.post(
        "/auth/login",
        json={
            "email": "cart@example.com",
            "password": "Password123!",
        },
    )

    client.headers["Authorization"] = (
        f"Bearer {login.json()['access_token']}"
    )

    return client


def test_create_cart(client):
    """A customer can create an empty cart."""
    response = client.post("/customers/me/cart")

    assert response.status_code == 201
    assert response.json()["status"] == "active"
    assert response.json()["items"] == []
    assert response.json()["restaurant_id"] is None


def test_create_cart_returns_existing(client):
    """Creating a cart twice returns the same active cart."""
    first = client.post("/customers/me/cart")
    second = client.post("/customers/me/cart")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert len(carts.repository.get_all()) == 1


def test_create_cart_requires_authentication(client):
    """A customer must sign in before creating a cart."""
    client.headers.pop("Authorization")

    response = client.post("/customers/me/cart")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_get_existing_cart(client):
    """Test retrieving an empty active cart with calculated totals."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    response = client.get("/customers/me/cart")

    assert response.status_code == 200
    assert response.json() == {
        **created.json(),
        "subtotal": 0,
        "total": 0,
        "problems": [],
    }


def test_get_cart_with_items_and_totals(client):
    """Test that GET cart returns item details and calculated totals."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    response = client.get("/customers/me/cart")

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 1
    assert data["items"][0] == {
        "menu_item_id": 1,
        "name": "Burger",
        "quantity": 2,
        "unit_price": 100,
        "line_total": 200,
        "problems": [],
    }
    assert data["subtotal"] == 200
    assert data["total"] == 200
    assert data["problems"] == []


def test_get_cart_not_found(client):
    """Return 404 when the customer has no active cart."""
    response = client.get("/customers/me/cart")

    assert response.status_code == 404
    assert response.json()["detail"] == "Active cart not found"
    assert carts.repository.get_all() == []


def test_get_cart_requires_authentication(client):
    """Reject requests from customers who are not signed in."""
    client.headers.pop("Authorization")

    response = client.get("/customers/me/cart")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_cart_storage_error(client):
    """Return 500 when the cart storage contains invalid JSON."""
    carts.repository.file_path.write_text("{invalid json}")

    post_response = client.post("/customers/me/cart")
    get_response = client.get("/customers/me/cart")

    assert post_response.status_code == 500
    assert post_response.json() == {
        "detail": "Cart storage is unavailable"
    }

    assert get_response.status_code == 500
    assert get_response.json() == {
        "detail": "Cart storage is unavailable"
    }


def test_deactivated_customer_cannot_access_cart(client):
    """Reject cart request from a deactivated customer."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    deactivated = client.post("/customers/me/deactivate")
    assert deactivated.status_code == 200

    post_response = client.post("/customers/me/cart")
    get_response = client.get("/customers/me/cart")

    assert post_response.status_code == 403
    assert post_response.json()["detail"] == "Account is inactive"

    assert get_response.status_code == 403
    assert get_response.json()["detail"] == "Account is inactive"


def test_cart_persists_after_restart(client):
    """Verify that a cart remains saved in storage."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    saved_cart = CartRepo(
        carts.repository.file_path
    ).get_active_for_customer(created.json()["customer_id"])

    assert saved_cart is not None
    assert saved_cart["id"] == created.json()["id"]
    assert saved_cart["status"] == "active"


def test_cart_invalid_saved_data(client):
    """Return 500 when a saved cart contains invalid item data."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    cart = created.json()
    cart["items"] = [
        {"menu_item_id": 1, "quantity": 0}
    ]

    shopping_data = {
        "carts": [cart],
        "orders": [],
    }

    carts.repository.file_path.write_text(
        json.dumps(shopping_data)
    )

    post_response = client.post("/customers/me/cart")
    get_response = client.get("/customers/me/cart")

    assert post_response.status_code == 500
    assert post_response.json() == {
        "detail": "Cart storage is unavailable"
    }

    assert get_response.status_code == 500
    assert get_response.json() == {
        "detail": "Cart storage is unavailable"
    }


def test_add_cart_item(client):
    """Test adding an available menu item to the active cart."""
    client.post("/customers/me/cart")

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )

    assert response.status_code == 200

    cart = response.json()
    assert cart["restaurant_id"] == 1
    assert cart["items"] == [
        {
            "menu_item_id": 1,
            "quantity": 2,
        }
    ]


def test_add_existing_cart_item(client):
    """Test increasing the quantity of an existing cart item."""
    client.post("/customers/me/cart")

    client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 3,
        },
    )

    assert response.status_code == 200
    assert response.json()["items"] == [
        {
            "menu_item_id": 1,
            "quantity": 5,
        }
    ]


def test_add_unavailable_cart_item(client):
    """Test rejecting an unavailable menu item."""
    client.post("/customers/me/cart")

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 3,
            "quantity": 2,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Menu item is unavailable"
    }


def test_add_item_from_different_restaurant(client):
    """Test rejecting an item from a different restaurant."""
    client.post("/customers/me/cart")

    first_response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )
    assert first_response.status_code == 200

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 2,
            "quantity": 1,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Can't add items from different restaurants"
    }


def test_add_nonexistent_cart_item(client):
    """Test rejecting a menu item that does not exist."""
    client.post("/customers/me/cart")

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 67,
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Menu item not found"
    }


def test_add_deactivated_cart_item(client, monkeypatch, tmp_path):
    """Test rejecting a deactivated menu item."""
    menu_file = tmp_path / "deactivated_menu.json"

    menu_file.write_text(
        json.dumps([
            {
                "id": 4,
                "restaurant_id": 1,
                "name": "Salad",
                "price": 80,
                "available": True,
                "active": False,
            },
        ])
    )

    monkeypatch.setattr(carts.menu_repository, "file_path", menu_file)

    client.post("/customers/me/cart")

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 4,
            "quantity": 1,
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Menu item is unavailable"
    }

@pytest.mark.parametrize(
    "quantity",
    [0, -1, "2", True, 1.5, None],
)
def test_add_cart_item_invalid_quantity(client, quantity):
    """Test rejecting invalid cart item quantities."""
    client.post("/customers/me/cart")

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": quantity,
        },
    )

    assert response.status_code == 422


def test_add_item_without_active_cart(client):
    """Test rejecting an item when the customer has no active cart."""
    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Active cart not found"
    }


def test_added_cart_item_persists(client):
    """Test that an added cart item is saved to storage."""
    create_response = client.post("/customers/me/cart")
    assert create_response.status_code == 201

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )

    assert response.status_code == 200

    saved_cart = carts.repository.get_active_for_customer(
        create_response.json()["customer_id"]
    )

    assert saved_cart["restaurant_id"] == 1
    assert saved_cart["items"] == [
        {
            "menu_item_id": 1,
            "quantity": 2,
        }
    ]


def test_rejected_cart_item_does_not_change_cart(client):
    """Test that a rejected item leaves the cart unchanged."""
    client.post("/customers/me/cart")

    first_response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )
    assert first_response.status_code == 200

    rejected_response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 2,
            "quantity": 1,
        },
    )
    assert rejected_response.status_code == 409

    response = client.get("/customers/me/cart")

    assert response.status_code == 200
    assert response.json()["restaurant_id"] == 1
    assert response.json()["items"] == [
        {
            "menu_item_id": 1,
            "name": "Burger",
            "quantity": 2,
            "unit_price": 100,
            "line_total": 200,
            "problems": [],
        }
    ]
    assert response.json()["subtotal"] == 200
    assert response.json()["total"] == 200
    assert response.json()["problems"] == []


def test_add_cart_item_requires_authentication(client):
    """Test that an unauthenticated user can't add cart items."""
    client.headers.pop("Authorization")

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_add_cart_item_storage_error(client):
    """Test handling a cart storage error when adding an item."""
    client.post("/customers/me/cart")

    carts.repository.file_path.write_text("invalid json")

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Cart storage is unavailable"
    }


def test_customer_cannot_add_item_to_another_cart(client):
    """Test that customers can't modify another customer's cart."""
    first_cart = client.post("/customers/me/cart")
    assert first_cart.status_code == 201

    registration = client.post(
        "/customers",
        json={
            "name": "Second Customer",
            "email": "second@example.com",
            "password": "Password123!",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "second@example.com",
            "password": "Password123!",
        },
    )
    assert login.status_code == 200

    client.headers["Authorization"] = (
        f"Bearer {login.json()['access_token']}"
    )

    response = client.post(
        "/customers/me/cart/items",
        json={
            "menu_item_id": 1,
            "quantity": 2,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active cart not found"

    saved_cart = carts.repository.get_by_id(first_cart.json()["id"])

    assert saved_cart["customer_id"] == first_cart.json()["customer_id"]
    assert saved_cart["restaurant_id"] is None
    assert saved_cart["items"] == []


def test_customer_cannot_view_another_cart(client):
    """Test that customers can't view another customer's cart."""
    cart = client.post("/customers/me/cart")
    assert cart.status_code == 201

    registration = client.post(
        "/customers",
        json={
            "name": "Customer",
            "email": "cust@example.com",
            "password": "Password123!",
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/auth/login",
        json={
            "email": "cust@example.com",
            "password": "Password123!",
        },
    )
    assert login.status_code == 200

    client.headers["Authorization"] = (
        f"Bearer {login.json()['access_token']}"
    )

    response = client.get("/customers/me/cart")

    assert response.status_code == 404
    assert response.json()["detail"] == "Active cart not found"

    second_cart = client.post("/customers/me/cart")
    assert second_cart.status_code == 201

    response = client.get("/customers/me/cart")

    assert response.status_code == 200
    assert response.json()["id"] == second_cart.json()["id"]
    assert response.json()["customer_id"] == second_cart.json()["customer_id"]
    assert response.json()["id"] != cart.json()["id"]
    assert response.json()["items"] == []
    assert response.json()["total"] == 0

    saved_carts = carts.repository.get_by_id(cart.json()["id"])

    assert saved_carts["customer_id"] == cart.json()["customer_id"]
    assert saved_carts["items"] == []


def test_get_cart_with_unavailable_item(client):
    """Test that GET cart reports unavailable saved items."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    carts.repository.modify(
        created.json()["id"],
        lambda cart: cart.update({
            "restaurant_id": 1,
            "items": [
                {"menu_item_id": 3, "quantity": 2},
            ],
        }),
    )

    response = client.get("/customers/me/cart")

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == [
        {
            "menu_item_id": 3,
            "name": "Fries",
            "quantity": 2,
            "unit_price": 50,
            "line_total": 100,
            "problems": ["unavailable"],
        }
    ]
    assert data["subtotal"] == 100
    assert data["total"] == 100
    assert data["problems"] == ["unavailable"]

def test_get_cart_with_missing_item(client):
    """Test that GET cart reports missing menu items."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    carts.repository.modify(
        created.json()["id"],
        lambda cart: cart.update({
            "restaurant_id": 1,
            "items": [
                {"menu_item_id": 50, "quantity": 2},
            ],
        }),
    )

    response = client.get("/customers/me/cart")

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == [
        {
            "menu_item_id": 50,
            "name": None,
            "quantity": 2,
            "unit_price": None,
            "line_total": None,
            "problems": ["missing"],
        }
    ]
    assert data["subtotal"] == 0
    assert data["total"] == 0
    assert data["problems"] == ["missing"]


def test_get_cart_invalid_menu_data(client, monkeypatch):
    """Test that malformed menu data returns a 500 error."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    monkeypatch.setattr(
        carts.menu_repository,
        "get_all",
        lambda: [
            {
                "id": 1,
                "name": "Burger",
                "price": 100,
            }
        ],
    )

    response = client.get("/customers/me/cart")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Cart storage is unavailable"
    }


def test_get_cart_invalid_menu_price(client, monkeypatch):
    """Test that an invalid menu price returns a 500 error."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    monkeypatch.setattr(
        carts.menu_repository,
        "get_all",
        lambda: [
            {
                "id": 1,
                "restaurant_id": 1,
                "name": "Burger",
                "price": "100",
                "available": True,
            }
        ],
    )

    response = client.get("/customers/me/cart")

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Cart storage is unavailable"
    }
