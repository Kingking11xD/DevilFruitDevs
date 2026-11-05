from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.services import token_service
from main import app


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    path = tmp_path / "accounts.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(dependencies.repository, "file_path", path)
    monkeypatch.setattr(token_service, "sessions", {})

    client = TestClient(app)
    response = client.post("/customers", json={
        "name": "JimBOB", "email": "JimBOB@email.com", "password": "test-pw-jimbob"})
    assert response.status_code == 201

    response = client.post("/auth/login", json={
        "email": "JimBOB@email.com", "password": "test-pw-jimbob"})
    assert response.status_code == 200
    client.headers["Authorization"] = "Bearer " + response.json()["access_token"]
    return client


def test_profile_changes(client: TestClient) -> None:
    response = client.get("/customers/me")
    assert response.status_code == 200
    assert response.json()["name"] == "JimBOB"
    assert "password_hash" not in response.json()

    response = client.patch("/customers/me", json={"name": "Ram Altman"})
    assert response.status_code == 200
    assert response.json()["name"] == "Ram Altman"

    response = client.patch("/customers/me/address", json={
        "delivery_address": "123 Test Street"})
    assert response.status_code == 200
    assert response.json()["delivery_address"] == "123 Test Street"
    assert client.get("/customers/me").json() == response.json()

    response = client.post("/customers/me/deactivate")
    assert response.status_code == 200
    assert response.json()["active"] is False
    assert client.get("/customers/me").status_code == 403


def test_invalid_profile_requests(client: TestClient) -> None:
    assert client.patch("/customers/me", json={"name": ""}).status_code == 422
    assert client.patch("/customers/me/address", json={
        "delivery_address": ""}).status_code == 422
    assert client.patch("/customers/me", json={
        "name": "vegeta", "role": "admin"}).status_code == 422

    dependencies.repository.update(1, {"role": "admin"})
    assert client.get("/customers/me").status_code == 403

    client.headers.pop("Authorization")
    assert client.get("/customers/me").status_code == 401
