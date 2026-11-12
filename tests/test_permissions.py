from pathlib import Path

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api import dependencies
from app.repositories.account_repo import AccountRepo
from app.repositories.json_store import update_records
from app.services import token_service
from app.services.account_service import InactiveAccountError
from app.services.permissions import (
    PermissionDeniedError, ResourceNotFoundError, require_owner,
    require_restaurant_access)


def test_customer_ownership() -> None:
    account = {"id": 1, "role": "customer", "active": True}
    require_owner(account, 1)

    with pytest.raises(ResourceNotFoundError):
        require_owner(account, 2)

    for role in ["admin", "restaurant_user"]:
        account["role"] = role
        with pytest.raises(PermissionDeniedError):
            require_owner(account, 1)


@pytest.mark.parametrize("role", ["customer", "restaurant_user", "admin"])
def test_inactive_account_is_blocked(role: str) -> None:
    account = {
        "id": 1, "role": role, "active": False, "managed_restaurant_ids": [1]}

    with pytest.raises(InactiveAccountError):
        require_owner(account, 1)
    with pytest.raises(InactiveAccountError):
        require_restaurant_access(account, 1)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    path = tmp_path / "accounts.json"
    path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr(dependencies.repository, "file_path", path)
    monkeypatch.setattr(token_service, "sessions", {})
    AccountRepo(path).create("Test user", "test@example.com", "unused-hash")
    app = FastAPI()

    # test routes exercise the dependencies without changing endpoints
    @app.get("/admin", dependencies=[Depends(dependencies.get_current_admin)])
    def admin() -> dict:
        return {"ok": True}

    @app.get("/restaurants/{restaurant_id}/manage",
             dependencies=[Depends(dependencies.get_restaurant_manager)])
    def manage() -> dict:
        return {"ok": True}

    client = TestClient(app)
    token = token_service.create_access_token(1)
    client.headers["Authorization"] = "Bearer " + token
    return client


@pytest.mark.parametrize("role, admin_status, assigned_status, other_status", [
    ("customer", 403, 403, 403),
    ("restaurant_user", 403, 200, 403),
    ("admin", 200, 200, 200)])
def test_access_and_deactivation(
        client: TestClient, role: str, admin_status: int,
        assigned_status: int, other_status: int) -> None:
    assert client.get("/admin").status_code == 403
    assert client.get("/restaurants/1/manage").status_code == 403

    def set_role(records: list[dict]) -> None:
        records[0]["role"] = role
        records[0]["managed_restaurant_ids"] = [1]

    update_records(dependencies.repository.file_path, set_role)
    assert client.get("/admin").status_code == admin_status
    assert client.get("/restaurants/1/manage").status_code == assigned_status
    assert client.get("/restaurants/2/manage").status_code == other_status

    dependencies.repository.update(1, {"active": False})
    assert client.get("/admin").status_code == 403
    assert client.get("/restaurants/2/manage").status_code == 403


@pytest.mark.parametrize("path", ["/admin", "/restaurants/1/manage"])
def test_dependencies_require_sign_in(client: TestClient, path: str) -> None:
    client.headers.pop("Authorization")
    assert client.get(path).status_code == 401
    client.headers["Authorization"] = "Bearer invalid-token"
    assert client.get(path).status_code == 401
