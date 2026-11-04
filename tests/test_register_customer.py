from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.routes import customers
from app.repositories.account_repo import AccountRepo
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def accounts_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "accounts.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(customers.repository, "file_path", path)
    return path


@pytest.fixture
def details() -> dict[str, str]:
    return {
        "name": "JimBOB",
        "email": "JimBOB@email.com",
        "password": "test-pw-jimbob"}


def test_register_customer(accounts_file: Path, details: dict[str, str]) -> None:
    details["name"] = " JimBOB "
    details["password"] = "  test-pw-悟空  "
    response = client.post("/customers", json=details)

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "JimBOB",
        "email": "jimbob@email.com",
        "role": "customer",
        "active": True,
        "delivery_address": None}

    saved = AccountRepo(accounts_file).get_by_id(1)
    assert saved is not None
    assert customers.service.passwords.verify(details["password"], saved["password_hash"])
    assert not customers.service.passwords.verify(
        details["password"].strip(), saved["password_hash"])
    assert details["password"] not in response.text
    assert saved["password_hash"] not in response.text


def test_duplicate_email(accounts_file: Path, details: dict[str, str]) -> None:
    assert client.post("/customers", json=details).status_code == 201
    before = accounts_file.read_bytes()
    details["email"] = " JIMBOB@EMAIL.COM "

    response = client.post("/customers", json=details)

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already in use"}
    assert accounts_file.read_bytes() == before


def test_invalid_registration(accounts_file: Path, details: dict[str, str]) -> None:
    before = accounts_file.read_bytes()
    invalid_fields = [
        ("name", "   "),
        ("name", "x" * 101),
        ("email", "not-an-email"),
        ("password", "test-pw"),
        ("password", "x" * 129),
        ("role", "admin")]

    for field, value in invalid_fields:
        invalid = {**details, field: value}
        response = client.post("/customers", json=invalid)

        assert response.status_code == 422, f"Accepted invalid {field}"
        assert accounts_file.read_bytes() == before
        for problem in response.json()["detail"]:
            assert "input" not in problem
            assert "ctx" not in problem


def test_missing_field_does_not_expose_password(details: dict[str, str]) -> None:
    del details["name"]

    response = client.post("/customers", json=details)

    assert response.status_code == 422
    assert details["password"] not in response.text


def test_failed_save(
        details: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_save(source: Path, destination: Path) -> None:
        raise OSError(f"Cannot replace {destination}")

    monkeypatch.setattr("app.repositories.json_store.os.replace", fail_save)
    response = client.post("/customers", json=details)

    assert response.status_code == 500
    assert response.json() == {"detail": "Account could not be saved"}
