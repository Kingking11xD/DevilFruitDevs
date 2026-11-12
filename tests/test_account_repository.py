import json
from pathlib import Path

import pytest

from app.repositories.account_repo import AccountEmailExistsError, AccountRepo


@pytest.fixture
def repository(tmp_path: Path) -> AccountRepo:
    path = tmp_path / "accounts.json"
    path.write_text("[]", encoding="utf-8")
    return AccountRepo(path)


def test_create_account(repository: AccountRepo) -> None:
    account = repository.create("JimBOB", " JimBOB@email.com ", "test-pw")

    assert account == {
        "id": 1,
        "name": "JimBOB",
        "email": "jimbob@email.com",
        "password_hash": "test-pw",
        "role": "customer",
        "active": True,
        "delivery_address": None,
        "managed_restaurant_ids": []}

    reloaded = AccountRepo(repository.file_path)
    assert reloaded.get_by_id(1) == account
    assert reloaded.get_by_email(" JimBOB@email.com ") == account


@pytest.mark.parametrize("role, restaurant_ids", [
    ("admin", []), ("restaurant_user", [1, 2])])
def test_create_staff(
        repository: AccountRepo, role: str, restaurant_ids: list[int]) -> None:
    customer = repository.create("JimBOB", "JimBOB@email.com", "test-hash")
    staff = repository.create_staff(
        "Staff", " STAFF@example.com ", "staff-hash", role, restaurant_ids)

    assert staff["id"] == customer["id"] + 1
    assert staff["email"] == "staff@example.com"
    assert staff["role"] == role
    assert staff["managed_restaurant_ids"] == restaurant_ids
    assert staff["active"] is True

    reloaded = AccountRepo(repository.file_path)
    assert reloaded.get_by_id(staff["id"]) == staff
    assert reloaded.get_by_id(customer["id"]) == customer


@pytest.mark.parametrize("role, restaurant_ids", [
    ("customer", []), ("unknown", []), ("admin", [1]),
    ("restaurant_user", [0]), ("restaurant_user", [-1]),
    ("restaurant_user", [True]), ("restaurant_user", ["1"])])
def test_invalid_staff_keeps_data(
        repository: AccountRepo, role: str, restaurant_ids: list[int]) -> None:
    repository.create("JimBOB", "JimBOB@email.com", "test-hash")
    before = repository.file_path.read_bytes()

    with pytest.raises(ValueError):
        repository.create_staff(
            "Staff", "staff@example.com", "staff-hash", role, restaurant_ids)

    assert repository.file_path.read_bytes() == before


def test_ids_continue_after_reload(repository: AccountRepo) -> None:
    first = repository.create("JimBOB", "JimBOB@email.com", "test-pw")
    second = repository.create("vegeta", "vegeta@email.com", "test-pw")
    second["id"] = 8
    repository.file_path.write_text(json.dumps([second, first]), encoding="utf-8")

    reloaded = AccountRepo(repository.file_path)
    third = reloaded.create("Ram Altman", "ramaltman@email.com", "test-pw")

    assert third["id"] == 9
    assert reloaded.get_by_id(first["id"]) == first
    assert reloaded.get_by_id(second["id"]) == second


def test_duplicate_email_keeps_data(repository: AccountRepo) -> None:
    repository.create("JimBOB", "JimBOB@email.com", "test-pw")
    before = repository.file_path.read_bytes()

    with pytest.raises(AccountEmailExistsError):
        repository.create("Other", " JimBOB@email.com ", "other-hash")

    with pytest.raises(AccountEmailExistsError):
        repository.create_staff(
            "Other", " JIMBOB@email.com ", "other-hash", "admin", [])

    assert repository.file_path.read_bytes() == before


def test_update_account(repository: AccountRepo) -> None:
    account = repository.create("JimBOB", "JimBOB@email.com", "test-pw")
    other = repository.create("vegeta", "vegeta@email.com", "test-pw")
    expected = {**account, "name": "Ram Altman"}

    updated = repository.update(account["id"], {"name": "Ram Altman"})

    assert updated == expected
    reloaded = AccountRepo(repository.file_path)
    assert reloaded.get_by_id(account["id"]) == expected
    assert reloaded.get_by_id(other["id"]) == other
    assert repository.update(999, {"name": "Missing"}) is None

    before = repository.file_path.read_bytes()

    for changes in [
            {"role": "admin"}, {"id": 99}, {"active": True},
            {"name": "vegeta", "email": "vegeta@email.com"}]:
        with pytest.raises(ValueError):
            repository.update(account["id"], changes)

        assert repository.file_path.read_bytes() == before


def test_failed_save_keeps_accounts(
        repository: AccountRepo, monkeypatch: pytest.MonkeyPatch) -> None:
    account = repository.create("JimBOB", "JimBOB@email.com", "test-pw")
    before = repository.file_path.read_bytes()

    def fail_save(source: Path, destination: Path) -> None:
        raise OSError("Cannot save accounts")

    # simulate a failure when replacing the saved file
    monkeypatch.setattr("app.repositories.json_store.os.replace", fail_save)

    with pytest.raises(OSError):
        repository.create("vegeta", "vegeta@email.com", "test-pw")

    with pytest.raises(OSError):
        repository.create_staff(
            "Bulma", "bulma@email.com", "staff-hash", "admin", [])

    with pytest.raises(OSError):
        repository.update(account["id"], {"name": "Ram Altman"})

    assert repository.file_path.read_bytes() == before
    assert list(repository.file_path.parent.iterdir()) == [repository.file_path]
