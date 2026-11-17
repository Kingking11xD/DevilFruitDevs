from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.api.routes import restaurants
from app.repositories.json_store import update_records
from app.repositories.restaurant_repo import RestaurantRepo
from app.services import token_service
from main import app


@pytest.fixture
def create_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "restaurants.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(restaurants.repository, "file_path", path)
    return path

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """log in as an admin with temporary account data"""
    path = tmp_path / "accounts.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(dependencies.repository, "file_path", path)
    monkeypatch.setattr(token_service, "sessions", {})
    password_hash = dependencies.account_service.passwords.hash("test-password-123")
    dependencies.repository.create_staff(
        "Test Admin", "admin@example.com", password_hash, "admin", [])

    with TestClient(app) as test_client:
        response = test_client.post("/auth/login", json={
            "email": "admin@example.com", "password": "test-password-123"})
        assert response.status_code == 200
        test_client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
        yield test_client


def test_create_restaurant(client: TestClient, create_file: Path) -> None:
    data = {
        "name": "Baratie",
        "cuisine": "Seafood",
        "address": "East Blue",
    }

    response = client.post("/restaurants", json=data)

    expected = data.copy()
    expected["id"] = 1

    assert response.status_code == 201
    assert response.json() == expected
    assert client.get("/restaurants/1").json() == expected

    second = client.post("/restaurants", json=data) # next restaurant gets a new id

    assert second.status_code == 201
    assert second.json()["id"] == 2

    saved = [expected, second.json()]
    # browsing stays public
    client.headers.pop("Authorization")
    assert client.get("/restaurants/1").json() == expected
    assert client.get("/restaurants").json() == saved
    assert RestaurantRepo(create_file).get_all() == saved


def test_create_invalid(client: TestClient, create_file: Path) -> None:
    data = {
        "name": "Baratie",
        "cuisine": "Seafood",
        "address": "East Blue",
    }
    before = create_file.read_bytes()

    response = client.post("/restaurants", json={}) # missing required fields
    assert response.status_code == 422
    assert create_file.read_bytes() == before

    invalid_fields = [ # one invalid field at a time
        ("name", "   "),
        ("cuisine", "   "),
        ("address", "   "),
        ("name", None),
        ("name", 123),
        ("name", "x" * 101),
        ("cuisine", "x" * 101),
        ("address", "x" * 251),
        ("id", 99),
        ("extra", "not allowed"),
    ]

    for field, value in invalid_fields:
        invalid_data = data.copy()
        invalid_data[field] = value

        response = client.post("/restaurants", json=invalid_data)

        assert response.status_code == 422, f"Accepted invalid {field}"
        assert create_file.read_bytes() == before


def test_create_storage_error(client: TestClient, create_file: Path) -> None:
    create_file.unlink()

    response = client.post("/restaurants", json={
        "name": "Baratie",
        "cuisine": "Seafood",
        "address": "East Blue",
    })

    assert response.status_code == 500
    assert response.json() == {
        "detail": "Restaurant data could not be saved"
    }
    assert not create_file.exists()


def test_create_requires_sign_in(client: TestClient, create_file: Path) -> None:
    """missing or invalid tokens cant create restaurants"""
    before = create_file.read_bytes()

    for authorization in [None, "Bearer invalid-token"]:
        client.headers.pop("Authorization", None)
        if authorization is not None:
            client.headers["Authorization"] = authorization

        response = client.post("/restaurants", json={
            "name": "Baratie", "cuisine": "Seafood", "address": "East Blue"})

        assert response.status_code == 401
        assert create_file.read_bytes() == before


def test_create_requires_admin(client: TestClient, create_file: Path) -> None:
    """customers and restaurant staff cant create restaurants"""
    before = create_file.read_bytes()

    for role in ["customer", "restaurant_user"]:
        def change_role(records: list[dict]) -> None:
            records[0]["role"] = role

        update_records(dependencies.repository.file_path, change_role)
        response = client.post("/restaurants", json={
            "name": "Baratie", "cuisine": "Seafood", "address": "East Blue"})

        assert response.status_code == 403
        assert response.json()["detail"] == "Administrator account required"
        assert create_file.read_bytes() == before


def test_create_rejects_inactive_admin(client: TestClient, create_file: Path) -> None:
    """old admin token stops working after deactivation"""
    dependencies.repository.update(1, {"active": False})
    before = create_file.read_bytes()

    response = client.post("/restaurants", json={
        "name": "Baratie", "cuisine": "Seafood", "address": "East Blue"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is inactive"
    assert create_file.read_bytes() == before
