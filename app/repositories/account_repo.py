from pathlib import Path
from typing import Any

from app.repositories.json_store import data_path, read_records, update_records


class AccountEmailExistsError(Exception):
    pass


class AccountRepo:

    def __init__(self, file_path: str | Path | None = None) -> None:
        if file_path is None:
            self.file_path = data_path("accounts.json")
        else:
            self.file_path = Path(file_path)

    def get_by_id(self, account_id: int) -> dict[str, Any] | None:
        for account in read_records(self.file_path):
            if account["id"] == account_id:
                return account

        return None

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        email = email.strip().lower()

        for account in read_records(self.file_path):
            if account["email"] == email:
                return account

        return None

    def create(self, name: str, email: str, password_hash: str) -> dict[str, Any]:
        email = email.strip().lower()

        def add_account(records: list[dict]) -> dict[str, Any]:
            next_id = 1

            # check duplicates while the storage lock is held
            for account in records:
                if account["email"] == email:
                    raise AccountEmailExistsError("Email already in use")
                if account["id"] >= next_id:
                    next_id = account["id"] + 1

            new_account = {
                "id": next_id,
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "role": "customer",
                "active": True,
                "delivery_address": None,
                "managed_restaurant_ids": []}

            records.append(new_account)
            return new_account

        return update_records(self.file_path, add_account)

    def update(self, account_id: int, changes: dict[str, Any]) -> dict[str, Any] | None:
        for field in changes:
            if field not in {"name", "delivery_address", "active"}:
                raise ValueError("Account field cannot be updated")

        if "active" in changes and changes["active"] is not False:
            raise ValueError("Account can only be deactivated")

        def update_account(records: list[dict]) -> dict[str, Any] | None:
            for account in records:
                if account["id"] == account_id:
                    account.update(changes)
                    return account

            return None

        return update_records(self.file_path, update_account)
