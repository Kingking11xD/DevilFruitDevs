from pathlib import Path

import pytest

from app.repositories.account_repo import AccountRepo
from app.services.account_service import AccountService, InactiveAccountError


@pytest.fixture
def service(tmp_path: Path) -> AccountService:
    path = tmp_path / "accounts.json"
    path.write_text("[]", encoding="utf-8")
    return AccountService(AccountRepo(path))


def test_register_customer(service: AccountService) -> None:
    password = "test-pw-jimbob"
    account = service.register_customer(" JimBOB ", " JimBOB@email.com ", password)
    saved = service.repository.get_by_id(account["id"])

    assert saved == account
    assert account["password_hash"].startswith("$argon2id$")
    assert service.passwords.verify(password, account["password_hash"])
    assert password not in service.repository.file_path.read_text(encoding="utf-8")


def test_sign_in_after_reload(service: AccountService) -> None:
    account = service.register_customer("JimBOB", "JimBOB@email.com", "test-pw-jimbob")
    reloaded = AccountService(AccountRepo(service.repository.file_path))

    result = reloaded.authenticate(" JIMBOB@EMAIL.COM ", "test-pw-jimbob")

    assert result["id"] == account["id"]
    assert result["email"] == "jimbob@email.com"


def test_update_and_deactivate_account(service: AccountService) -> None:
    account = service.register_customer("JimBOB", "JimBOB@email.com", "test-pw-jimbob")
    account_id = account["id"]

    assert service.update_name(account_id, "  Ram Altman  ")["name"] == "Ram Altman"
    assert service.update_address(
        account_id, "  123 Test Street  ")["delivery_address"] == "123 Test Street"
    assert service.deactivate(account_id)["active"] is False

    with pytest.raises(InactiveAccountError):
        service.update_name(account_id, "vegeta")

    assert service.repository.get_by_id(account_id) is not None
