from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Any

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api import dependencies
from app.api.dependencies import get_current_account
from app.repositories.json_store import update_records
from app.services import token_service
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def accounts_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "accounts.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(dependencies.repository, "file_path", path)
    monkeypatch.setattr(token_service, "sessions", {})
    return path


@pytest.fixture
def account() -> dict[str, Any]:
    response = client.post("/customers", json={
        "name": "JimBOB", "email": "JimBOB@email.com", "password": "test-pw-jimbob"})
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def protected_client() -> TestClient:
    test_app = FastAPI()

    # this route exists only in tests to check the shared authentication helper
    @test_app.get("/protected")
    def protected(account: Annotated[dict[str, Any], Depends(get_current_account)]) -> dict[str, int]:
        return {"id": account["id"]}

    return TestClient(test_app)


def test_sign_in(account: dict[str, Any], protected_client: TestClient) -> None:
    before = datetime.now(timezone.utc)
    token_service.sessions["expired"] = {
        "account_id": account["id"], "expires_at": before - timedelta(minutes=1)}
    response = client.post("/auth/login", json={
        "email": " JIMBOB@EMAIL.COM ", "password": "test-pw-jimbob"})

    assert response.status_code == 200
    result = response.json()
    assert result["token_type"] == "bearer"
    assert result["expires_in"] == 1800
    assert set(result) == {"access_token", "token_type", "expires_in"}
    session = token_service.sessions[result["access_token"]]
    assert session["account_id"] == account["id"]
    assert before + timedelta(minutes=30) <= session["expires_at"] <= datetime.now(timezone.utc) + timedelta(minutes=30)
    assert "expired" not in token_service.sessions
    protected = protected_client.get(
        "/protected", headers={"Authorization": f"Bearer {result['access_token']}"})
    assert protected.status_code == 200
    assert protected.json() == {"id": account["id"]}


def test_invalid_sign_in(account: dict[str, Any]) -> None:
    for email, password in [
            ("vegeta@email.com", "test-pw-jimbob"),
            ("JimBOB@email.com", "wrong-password")]:
        response = client.post("/auth/login", json={"email": email, "password": password})
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid email or password"}

    response = client.post("/auth/login", json={"password": "test-pw-jimbob"})
    assert response.status_code == 422
    assert "test-pw-jimbob" not in response.text


def test_invalid_tokens(account: dict[str, Any], protected_client: TestClient) -> None:
    token = token_service.create_access_token(account["id"])
    token_service.sessions[token]["expires_at"] = datetime.now(timezone.utc) - timedelta(minutes=1)

    assert protected_client.get("/protected").status_code == 401
    for invalid in ["not-a-token", token + "changed", token]:
        response = protected_client.get("/protected", headers={"Authorization": f"Bearer {invalid}"})
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    assert token not in token_service.sessions


def test_account_changes_block_old_token(
        account: dict[str, Any], accounts_file: Path, protected_client: TestClient) -> None:
    response = client.post("/auth/login", json={
        "email": "JimBOB@email.com", "password": "test-pw-jimbob"})
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

    def deactivate(records: list[dict]) -> None:
        records[0]["active"] = False

    update_records(accounts_file, deactivate)
    assert protected_client.get("/protected", headers=headers).status_code == 403
    assert client.post("/auth/login", json={
        "email": "JimBOB@email.com", "password": "test-pw-jimbob"}).status_code == 403

    def remove_account(records: list[dict]) -> None:
        records.clear()

    update_records(accounts_file, remove_account)
    assert protected_client.get("/protected", headers=headers).status_code == 401


def test_session_reset_requires_sign_in(account: dict[str, Any], protected_client: TestClient) -> None:
    response = client.post("/auth/login", json={
        "email": "JimBOB@email.com", "password": "test-pw-jimbob"})
    old_token = response.json()["access_token"]

    # restarting the backend clears the sessions but keeps the saved accounts
    token_service.sessions.clear()
    assert protected_client.get(
        "/protected", headers={"Authorization": f"Bearer {old_token}"}).status_code == 401

    response = client.post("/auth/login", json={
        "email": "JimBOB@email.com", "password": "test-pw-jimbob"})
    assert response.status_code == 200
    new_token = response.json()["access_token"]
    assert new_token != old_token
    assert protected_client.get(
        "/protected", headers={"Authorization": f"Bearer {new_token}"}).json() == {"id": account["id"]}
