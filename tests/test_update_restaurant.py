import json
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


ORIGINAL = {
    "id": 1,
    "name": "Baratie",
    "cuisine": "Seafood",
    "address": "East Blue",
}


@pytest.fixture
def update_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps([ORIGINAL]), encoding="utf-8")
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


def set_account_role(role: str, restaurant_ids: list[int]) -> None:
    """change the saved role and assignments for this test"""
    def change_role(records: list[dict]) -> None:
        records[0]["role"] = role
        records[0]["managed_restaurant_ids"] = restaurant_ids

    update_records(dependencies.repository.file_path, change_role)


def test_update_restaurant(client: TestClient, update_file: Path) -> None:
    response = client.patch("/restaurants/1", json={
        "address": "  Water 7  ",
    })

    expected = ORIGINAL.copy()
    expected["address"] = "Water 7"

    assert response.status_code == 200
    assert response.json() == expected
    assert client.get("/restaurants/1").json() == expected
    assert RestaurantRepo(update_file).get_all() == [expected]


def test_update_invalid(client: TestClient, update_file: Path) -> None:
    before = update_file.read_bytes()

    invalid_updates = [
        {},
        {"name": "   "},
        {"cuisine": "   "},
        {"address": "   "},
        {"name": None},
        {"cuisine": None},
        {"address": None},
        {"name": 123},
        {"name": "x" * 101},
        {"cuisine": "x" * 101},
        {"address": "x" * 251},
        {"id": 99},
        {"extra": "value"},
        {"name": "Valid Name", "address": None},
    ]

    for changes in invalid_updates:
        response = client.patch("/restaurants/1", json=changes)

        assert response.status_code == 422, f"Accepted {changes}"
        assert update_file.read_bytes() == before


def test_update_errors(client: TestClient, update_file: Path) -> None:
    before = update_file.read_bytes()

    response = client.patch("/restaurants/999", json={"name": "Cafe"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant not found"}
    assert update_file.read_bytes() == before

    # missing file is a storage error
    update_file.unlink()
    response = client.patch("/restaurants/1", json={"name": "Cafe"})

    assert response.status_code == 500
    assert response.json() == {"detail": "Restaurant data not saved"}
    assert not update_file.exists()


def test_update_requires_sign_in(client: TestClient, update_file: Path) -> None:
    """missing or invalid tokens cant update restaurants"""
    before = update_file.read_bytes()

    for authorization in [None, "Bearer invalid-token"]:
        client.headers.pop("Authorization", None)
        if authorization is not None:
            client.headers["Authorization"] = authorization

        response = client.patch("/restaurants/1", json={"name": "Changed Name"})

        assert response.status_code == 401
        assert update_file.read_bytes() == before


def test_update_checks_restaurant_access(client: TestClient, update_file: Path) -> None:
    """staff can only update their assigned restaurants"""
    cases = [
        ("restaurant_user", [2], 403),
        ("restaurant_user", [], 403),
        ("customer", [], 403),
        ("restaurant_user", [1], 200)]

    for role, restaurant_ids, expected_status in cases:
        set_account_role(role, restaurant_ids)
        before = update_file.read_bytes()

        response = client.patch("/restaurants/1", json={"name": "Changed Name"})

        assert response.status_code == expected_status
        if expected_status == 200:
            expected = ORIGINAL.copy()
            expected["name"] = "Changed Name"
            assert response.json() == expected
            assert RestaurantRepo(update_file).get_all() == [expected]
        else:
            assert update_file.read_bytes() == before


@pytest.mark.parametrize("role", ["admin", "restaurant_user"])
def test_update_rejects_inactive_accounts(
        client: TestClient, update_file: Path, role: str) -> None:
    """old tokens cant update restaurants after deactivation"""
    restaurant_ids = [1] if role == "restaurant_user" else []
    set_account_role(role, restaurant_ids)
    dependencies.repository.update(1, {"active": False})
    before = update_file.read_bytes()

    response = client.patch("/restaurants/1", json={"name": "Changed Name"})

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is inactive"
    assert update_file.read_bytes() == before
