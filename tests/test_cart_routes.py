"""Tests for shopping cart API routes"""

import pytest
import json
from fastapi.testclient import TestClient

from main import app
from app.api import dependencies
from app.api.routes import carts
from app.services import token_service
from app.repositories.cart_repo import CartRepo
from app.repositories.json_store import update_records
from app.repositories import json_store

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


def test_add_item_invalid_saved_cart_unchanged(client):
    """Test that a failed addition doesn't modify an invalid cart."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    cart = created.json()
    cart["restaurant_id"] = 1
    cart["items"] = [
        {"menu_item_id": 3, "quantity": 0}
    ]

    shopping_data = {
        "carts": [cart],
        "orders": [],
    }

    carts.repository.file_path.write_text(
        json.dumps(shopping_data)
    )

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

    saved_cart = carts.repository.get_by_id(cart["id"])
    assert saved_cart == cart


def test_update_cart_item_quantity(client):
    """Test updating an item's quantity and recalculating totals."""
    client.post("/customers/me/cart")

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    response = client.patch(
        "/customers/me/cart/items/1",
        json={"quantity": 5},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["items"][0]["menu_item_id"] == 1
    assert data["items"][0]["quantity"] == 5
    assert data["items"][0]["line_total"] == 500
    assert data["subtotal"] == 500
    assert data["total"] == 500

    saved_cart = carts.repository.get_active_for_customer(
        data["customer_id"]
    )
    assert saved_cart["items"][0]["quantity"] == 5


@pytest.mark.parametrize("quantity", [0, -1, 2.5, True, "5", None])
def test_update_cart_item_invalid_quantity(client, quantity):
    """Test that invalid quantities return 422 without changing the cart."""
    client.post("/customers/me/cart")

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    customer_id = added.json()["customer_id"]
    original_cart = carts.repository.get_active_for_customer(customer_id)

    response = client.patch(
        "/customers/me/cart/items/1",
        json={"quantity": quantity},
    )

    assert response.status_code == 422

    saved_cart = carts.repository.get_active_for_customer(customer_id)
    assert saved_cart == original_cart


def test_update_cart_item_missing_item(client):
    """Test that updating a missing cart item returns 404."""
    client.post("/customers/me/cart")

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    customer_id = added.json()["customer_id"]
    original_cart = carts.repository.get_active_for_customer(customer_id)

    response = client.patch(
        "/customers/me/cart/items/999",
        json={"quantity": 5},
    )

    assert response.status_code == 404

    saved_cart = carts.repository.get_active_for_customer(customer_id)
    assert saved_cart == original_cart


def test_update_cart_item_without_active_cart(client):
    """Test that updating an item without an active cart returns 404."""
    response = client.patch(
        "/customers/me/cart/items/1",
        json={"quantity": 5},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Active cart not found"
    }
    assert carts.repository.get_all() == []


def test_update_cart_item_requires_authentication(client):
    """Test that unauthenticated users can't update cart quantities."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    customer_id = created.json()["customer_id"]
    original_cart = carts.repository.get_active_for_customer(customer_id)

    client.headers.pop("Authorization")

    response = client.patch(
        "/customers/me/cart/items/1",
        json={"quantity": 5},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"

    saved_cart = carts.repository.get_active_for_customer(customer_id)
    assert saved_cart == original_cart


def test_deactivated_customer_cannot_update_cart_item(client):
    """Test that inactive customers can't update cart quantities."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    customer_id = created.json()["customer_id"]
    original_cart = carts.repository.get_active_for_customer(customer_id)

    deactivated = client.post("/customers/me/deactivate")
    assert deactivated.status_code == 200

    response = client.patch(
        "/customers/me/cart/items/1",
        json={"quantity": 5},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is inactive"

    saved_cart = carts.repository.get_active_for_customer(customer_id)
    assert saved_cart == original_cart


def test_customer_cannot_update_another_cart(client):
    """Test that customers can't update another customer's cart."""
    first_cart = client.post("/customers/me/cart")
    assert first_cart.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    original_cart = carts.repository.get_by_id(first_cart.json()["id"])

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

    response = client.patch(
        "/customers/me/cart/items/1",
        json={"quantity": 5},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Active cart not found"

    saved_cart = carts.repository.get_by_id(first_cart.json()["id"])
    assert saved_cart == original_cart


def test_update_cart_item_invalid_saved_cart_unchanged(client):
    """Test that invalid saved cart data is rejected without modification."""
    client.post("/customers/me/cart")

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    shopping = json.loads(cart_file.read_text())
    shopping["carts"][0]["items"][0]["quantity"] = 0
    cart_file.write_text(json.dumps(shopping))

    original_data = cart_file.read_text()

    response = client.patch(
        "/customers/me/cart/items/1",
        json={"quantity": 5},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Cart storage is unavailable"
    assert cart_file.read_text() == original_data


def test_update_cart_item_storage_error(client, monkeypatch):
    """Test that a storage failure returns 500 without changing the cart."""
    client.post("/customers/me/cart")

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    def fail_modify(cart_id, change):
        """Simulate a failure while saving the cart."""
        raise OSError("Storage failure")

    monkeypatch.setattr(carts.repository, "modify", fail_modify)

    response = client.patch(
        "/customers/me/cart/items/1",
        json={"quantity": 5},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Cart storage is unavailable"
    assert cart_file.read_text() == original_data


@pytest.mark.parametrize("item_id", [0, -1, "abc"])
def test_update_cart_item_invalid_id(client, item_id):
    """Test that invalid item IDs return 422."""
    response = client.patch(
        f"/customers/me/cart/items/{item_id}",
        json={"quantity": 5},
    )

    assert response.status_code == 422
    assert carts.repository.get_all() == []


def test_remove_last_cart_item(client):
    """Test DELETE removes the last item and updates the cart."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    response = client.delete("/customers/me/cart/items/1")

    assert response.status_code == 204
    assert response.content == b""

    saved_cart = carts.repository.get_active_for_customer(
        created.json()["customer_id"]
    )
    assert saved_cart["items"] == []
    assert saved_cart["restaurant_id"] is None

    details = client.get("/customers/me/cart")
    assert details.status_code == 200
    assert details.json()["items"] == []
    assert details.json()["subtotal"] == 0
    assert details.json()["total"] == 0


def test_remove_cart_item_keeps_other_items(client):
    """Test DELETE removes only the requested item and updates totals."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    repo = carts.repository
    cart = repo.get_active_for_customer(created.json()["customer_id"])

    repo.modify(
        cart["id"],
        lambda current: current["items"].append({
            "menu_item_id": 3,
            "quantity": 3,
        }),
    )

    response = client.delete("/customers/me/cart/items/1")

    assert response.status_code == 204
    assert response.content == b""

    saved_cart = repo.get_active_for_customer(created.json()["customer_id"])
    assert saved_cart["items"] == [
        {"menu_item_id": 3, "quantity": 3}
    ]
    assert saved_cart["restaurant_id"] == 1

    details = client.get("/customers/me/cart")
    assert details.status_code == 200
    assert details.json()["subtotal"] == 150
    assert details.json()["total"] == 150


def test_remove_cart_item_not_found(client):
    """Test DELETE returns 404 and keeps the cart unchanged."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    response = client.delete("/customers/me/cart/items/20")

    assert response.status_code == 404
    assert response.json() == {"detail": "Cart item not found"}
    assert cart_file.read_text() == original_data


def test_remove_cart_item_no_active_cart(client):
    """Test DELETE returns 404 when no active cart exists."""
    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    response = client.delete("/customers/me/cart/items/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Active cart not found"}
    assert cart_file.read_text() == original_data


def test_remove_cart_item_requires_authentication(client):
    """Test DELETE requires authentication and preserves cart data."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    client.headers.pop("Authorization")

    response = client.delete("/customers/me/cart/items/1")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}
    assert cart_file.read_text() == original_data


def test_remove_cart_item_deactivated_customer(client):
    """Test that inactive customers can't remove cart items."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    deactivated = client.post("/customers/me/deactivate")
    assert deactivated.status_code == 200

    response = client.delete("/customers/me/cart/items/1")

    assert response.status_code == 403
    assert response.json() == {"detail": "Account is inactive"}
    assert cart_file.read_text() == original_data


def test_customer_cannot_remove_another_cart_item(client):
    """Test that customers can't remove another customer's items."""
    first_cart = client.post("/customers/me/cart")
    assert first_cart.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

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

    response = client.delete("/customers/me/cart/items/1")

    assert response.status_code == 404
    assert response.json() == {"detail": "Active cart not found"}
    assert cart_file.read_text() == original_data


def test_remove_cart_item_invalid_saved_data_unchanged(client):
    """Test DELETE rejects invalid saved data without modifying it."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    shopping = json.loads(cart_file.read_text())
    shopping["carts"][0]["items"][0]["quantity"] = 0
    cart_file.write_text(json.dumps(shopping))

    original_data = cart_file.read_text()

    response = client.delete("/customers/me/cart/items/1")

    assert response.status_code == 500
    assert response.json() == {"detail": "Cart storage is unavailable"}
    assert cart_file.read_text() == original_data


def test_remove_cart_item_storage_error(client):
    """Test DELETE handles invalid JSON without changing saved data."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    cart_file.write_text("{invalid json}")
    original_data = cart_file.read_text()

    response = client.delete("/customers/me/cart/items/1")

    assert response.status_code == 500
    assert response.json() == {"detail": "Cart storage is unavailable"}
    assert cart_file.read_text() == original_data


@pytest.mark.parametrize("item_id", [0, -1, "abc"])
def test_remove_cart_item_invalid_id(client, item_id):
    """Test DELETE rejects invalid item IDs without changing saved data."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    response = client.delete(f"/customers/me/cart/items/{item_id}")

    assert response.status_code == 422
    assert cart_file.read_text() == original_data


def test_clear_cart_removes_items_and_resets_totals(client):
    """Test that clearing a cart removes its items and resets totals."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    def add_second_item(cart):
        """Add another menu item to test clearing all items."""
        cart["items"].append({"menu_item_id": 3, "quantity": 1})

    carts.repository.modify(created.json()["id"], add_second_item)

    saved_cart = carts.repository.get_by_id(created.json()["id"])
    assert len(saved_cart["items"]) == 2

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 204
    assert response.content == b""

    cart = client.get("/customers/me/cart")
    assert cart.status_code == 200

    data = cart.json()
    assert data["items"] == []
    assert data["restaurant_id"] is None
    assert data["status"] == "active"
    assert data["subtotal"] == 0
    assert data["total"] == 0
    assert data["problems"] == []


def test_clear_already_empty_cart(client):
    """Test that clearing an already empty cart succeeds."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    first_clear = client.delete("/customers/me/cart/items")
    assert first_clear.status_code == 204

    second_clear = client.delete("/customers/me/cart/items")
    assert second_clear.status_code == 204
    assert second_clear.content == b""

    cart = client.get("/customers/me/cart")
    assert cart.status_code == 200
    assert cart.json()["items"] == []
    assert cart.json()["restaurant_id"] is None
    assert cart.json()["subtotal"] == 0
    assert cart.json()["total"] == 0


def test_clear_cart_no_active_cart(client):
    """Test that clearing a missing cart returns 404."""
    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 404
    assert response.json()["detail"] == "Active cart not found"


def test_clear_cart_requires_authentication(client):
    """Test that an unauthenticated user can't clear a cart."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    original_cart = carts.repository.get_by_id(created.json()["id"])

    client.headers.pop("Authorization")

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"

    saved_cart = carts.repository.get_by_id(created.json()["id"])
    assert saved_cart == original_cart


def test_clear_cart_deactivated_customer(client):
    """Test that an inactive customer can't clear their cart."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    deactivated = client.post("/customers/me/deactivate")
    assert deactivated.status_code == 200

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is inactive"
    assert cart_file.read_text() == original_data


def test_customer_cannot_clear_another_cart(client):
    """Test that customers can't clear another customer's cart."""
    first_cart = client.post("/customers/me/cart")
    assert first_cart.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

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

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 404
    assert response.json() == {"detail": "Active cart not found"}
    assert cart_file.read_text() == original_data


def test_clear_cart_persists_empty_cart(client):
    """Test that clearing a cart persists the changes to storage."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    response = client.delete("/customers/me/cart/items")
    assert response.status_code == 204

    cart_file = carts.repository.file_path
    shopping = json.loads(cart_file.read_text())

    saved_cart = next(
        cart for cart in shopping["carts"]
        if cart["id"] == created.json()["id"]
    )

    assert saved_cart["items"] == []
    assert saved_cart["restaurant_id"] is None
    assert saved_cart["status"] == "active"


def test_clear_cart_invalid_saved_data_unchanged(client):
    """Test that clearing invalid saved cart data returns 500."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    shopping = json.loads(cart_file.read_text())

    saved_cart = next(
        cart for cart in shopping["carts"]
        if cart["id"] == created.json()["id"]
    )
    saved_cart["items"][0]["quantity"] = 0
    cart_file.write_text(json.dumps(shopping))

    original_data = cart_file.read_text()

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 500
    assert response.json()["detail"] == "Cart storage is unavailable"
    assert cart_file.read_text() == original_data


def test_clear_cart_storage_error(client, monkeypatch):
    """Test that a storage failure leaves the cart unchanged."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    def fail_modify(cart_id, change):
        """Simulate a repository storage failure."""
        raise OSError("Storage failure")

    monkeypatch.setattr(carts.repository, "modify", fail_modify)

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 500
    assert response.json()["detail"] == "Cart storage is unavailable"
    assert cart_file.read_text() == original_data


def test_clear_cart_preserves_other_carts_and_orders(client):
    """Test that clearing a cart preserves unrelated saved data."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    shopping = json.loads(cart_file.read_text())

    original_cart = shopping["carts"][0]

    other_cart = {
        "id": original_cart["id"] + 1000,
        "customer_id": original_cart["customer_id"] + 1000,
        "restaurant_id": original_cart["restaurant_id"],
        "status": "active",
        "items": [item.copy() for item in original_cart["items"]]
    }

    shopping["carts"].append(other_cart)
    shopping["orders"].append({"id": 999, "marker": "unchanged"})
    cart_file.write_text(json.dumps(shopping))

    response = client.delete("/customers/me/cart/items")
    assert response.status_code == 204

    saved = json.loads(cart_file.read_text())

    assert saved["carts"][0]["items"] == []
    assert saved["carts"][0]["restaurant_id"] is None
    assert saved["carts"][1] == other_cart
    assert saved["orders"] == shopping["orders"]


def test_clear_cart_invalid_authentication(client):
    """Test that an invalid token can't clear a cart."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    client.headers["Authorization"] = "Bearer invalid-token"

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication"
    assert cart_file.read_text() == original_data


@ pytest.mark.parametrize("role", ["admin", "restaurant_user"])
def test_clear_cart_rejects_non_customer_role(client, role):
    """Test that non customer accounts can't clear carts."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    def change_role(records):
        """Change the customer's role for testing."""
        records[0]["role"] = role

    update_records(dependencies.repository.file_path, change_role)

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 403
    assert response.json()["detail"] == "Customer account required"
    assert cart_file.read_text() == original_data


def test_clear_cart_failed_save_unchanged(client, monkeypatch):
    """Test that a failed save preserves the original cart."""
    created = client.post("/customers/me/cart")
    assert created.status_code == 201

    added = client.post(
        "/customers/me/cart/items",
        json={"menu_item_id": 1, "quantity": 2},
    )
    assert added.status_code == 200

    cart_file = carts.repository.file_path
    original_data = cart_file.read_text()

    def fail_replace(source, destination):
        """Simulate a failure replacing the saved file."""
        raise OSError("Simulated save failure")

    monkeypatch.setattr(json_store.os, "replace", fail_replace)

    response = client.delete("/customers/me/cart/items")

    assert response.status_code == 500
    assert response.json()["detail"] == "Cart storage is unavailable"
    assert cart_file.read_text() == original_data
