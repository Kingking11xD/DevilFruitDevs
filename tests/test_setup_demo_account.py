from pathlib import Path

import pytest

import setup_demo_account
from app.repositories.account_repo import AccountRepo
from app.services.account_service import AccountService


DETAILS = ["--name", " Bulma ", "--email", " BULMA@email.com "]
PASSWORD = "  test-pw-bulma  "


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "accounts.json").write_text("[]", encoding="utf-8")
    (tmp_path / "restaurants.json").write_text('[{"id": 1}, {"id": 2}]', encoding="utf-8")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))

    def password(prompt: str) -> str:
        return PASSWORD

    monkeypatch.setattr(setup_demo_account, "getpass", password)
    return tmp_path


@pytest.mark.parametrize("role, restaurant_ids", [
    ("admin", []), ("restaurant_user", [1, 2])])
def test_create_and_repeat_setup(
        data_dir: Path, capsys: pytest.CaptureFixture,
        role: str, restaurant_ids: list[int]) -> None:
    args = DETAILS + ["--role", role]
    for restaurant_id in restaurant_ids:
        args.extend(["--restaurant-id", str(restaurant_id)])

    assert setup_demo_account.main(args) == 0
    path = data_dir / "accounts.json"
    account = AccountRepo(path).get_by_email("bulma@email.com")
    assert account["name"] == "Bulma"
    assert account["email"] == "bulma@email.com"
    assert account["role"] == role
    assert account["managed_restaurant_ids"] == restaurant_ids
    assert account["password_hash"].startswith("$argon2id$")
    assert PASSWORD not in path.read_text(encoding="utf-8")
    assert AccountService(AccountRepo(path)).authenticate("bulma@email.com", PASSWORD) == account
    before = path.read_bytes()

    assert setup_demo_account.main(args) == 1
    assert path.read_bytes() == before
    output = capsys.readouterr()
    assert f"Created {role} account" in output.out
    assert "Email already in use" in output.err
    assert PASSWORD not in output.out + output.err
    assert account["password_hash"] not in output.out + output.err


@pytest.mark.parametrize("passwords, restaurant_id, message", [
    ([PASSWORD, "different"], 1, "Passwords do not match"),
    (["short", "short"], 1, "Invalid name, email or password"),
    ([PASSWORD, PASSWORD], 99, "Restaurant 99 not found")])
def test_invalid_setup(
        data_dir: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture,
        passwords: list[str], restaurant_id: int, message: str) -> None:
    answers = iter(passwords)

    def password(prompt: str) -> str:
        return next(answers)

    monkeypatch.setattr(setup_demo_account, "getpass", password)
    path = data_dir / "accounts.json"
    AccountRepo(path).create("JimBOB", "jimbob@email.com", "test-hash")
    before = path.read_bytes()
    args = DETAILS + ["--role", "restaurant_user", "--restaurant-id", str(restaurant_id)]

    assert setup_demo_account.main(args) == 1
    assert path.read_bytes() == before
    output = capsys.readouterr()
    assert message in output.err
    assert passwords[0] not in output.out + output.err


@pytest.mark.parametrize("contents", [None, "broken json"])
def test_storage_error(
        data_dir: Path, capsys: pytest.CaptureFixture, contents: str | None) -> None:
    path = data_dir / "accounts.json"
    if contents is None:
        path.unlink()
    else:
        path.write_text(contents, encoding="utf-8")

    assert setup_demo_account.main(DETAILS + ["--role", "admin"]) == 1
    assert "Could not read or save demo data" in capsys.readouterr().err
    if contents is None:
        assert not path.exists()
    else:
        assert path.read_text(encoding="utf-8") == contents
