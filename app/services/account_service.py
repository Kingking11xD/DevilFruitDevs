from typing import Any

from pwdlib import PasswordHash

from app.repositories.account_repo import AccountEmailExistsError, AccountRepo


class AccountExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class InactiveAccountError(Exception):
    pass


class AccountService:

    def __init__(self, repository: AccountRepo) -> None:
        self.repository = repository
        self.passwords = PasswordHash.recommended()

    def register_customer(
            self, name: str, email: str, password: str) -> dict[str, Any]:
        password_hash = self.passwords.hash(password)

        try:
            return self.repository.create(name.strip(), email, password_hash)
        except AccountEmailExistsError as error:
            raise AccountExistsError("Email already in use") from error

    def authenticate(self, email: str, password: str) -> dict[str, Any]:
        account = self.repository.get_by_email(email)

        if account is None:
            raise InvalidCredentialsError("Invalid email or password")

        if not self.passwords.verify(password, account["password_hash"]):
            raise InvalidCredentialsError("Invalid email or password")

        if not account["active"]:
            raise InactiveAccountError("Account is inactive")

        return account

    def get_active_account(self, account_id: int) -> dict[str, Any]:
        # load the current account so old tokens cannot bypass deactivation
        account = self.repository.get_by_id(account_id)

        if account is None:
            raise InvalidCredentialsError("Invalid authentication")

        if not account["active"]:
            raise InactiveAccountError("Account is inactive")

        return account

    def update_name(self, account_id: int, name: str) -> dict[str, Any]:
        return self._update_account(account_id, {"name": name.strip()})

    def update_address(self, account_id: int, address: str) -> dict[str, Any]:
        return self._update_account(
            account_id, {"delivery_address": address.strip()})

    def deactivate(self, account_id: int) -> dict[str, Any]:
        return self._update_account(account_id, {"active": False})

    def _update_account(self, account_id: int, changes: dict[str, Any]) -> dict[str, Any]:
        self.get_active_account(account_id)
        account = self.repository.update(account_id, changes)

        if account is None:
            raise InvalidCredentialsError("Invalid authentication")

        return account
