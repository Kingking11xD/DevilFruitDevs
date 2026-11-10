"""Tests for shopping cart API routes"""

import pytest
from fastapi.testclient import TestClient

from main import app
from app.api import dependencies
from app.api.routes import carts
from app.services import token_service

@pytest.fixture
def client(tmp_path, monkeypatch):
    """Create an authenticated customer with temporary storage."""
    accounts_path = tmp_path / "accounts.json"
    accounts_path.write_text("[]")

    shopping_path = tmp_path / "shopping.json"
    shopping_path.write_text('{"carts": [], "orders": []}')

    monkeypatch.setattr(
        dependencies.repository, "file_path", accounts_path
    )
    monkeypatch.setattr(
        carts.repository, "file_path", shopping_path
    )
    monkeypatch.setattr(token_service, "sessions", {})

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
    """Return the customer's existing active cart."""
    created = client.post("/customers/me/cart")

    response = client.get("/customers/me/cart")

    assert created.status_code == 201
    assert response.status_code == 200
    assert response.json() == created.json()

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