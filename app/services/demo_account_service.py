from typing import Any

from pydantic import ValidationError
from pwdlib import PasswordHash

from app.repositories.account_repo import AccountEmailExistsError, AccountRepo
from app.repositories.restaurant_repo import RestaurantRepo
from app.schemas.account import AccountCreate
from app.services.account_service import AccountExistsError


class DemoAccountError(Exception):
    pass


class DemoAccountService:

    def __init__(self, accounts: AccountRepo, restaurants: RestaurantRepo) -> None:
        self.accounts = accounts
        self.restaurants = restaurants
        self.passwords = PasswordHash.recommended()

    def create(
            self, name: str, email: str, password: str,
            role: str, restaurant_ids: list[int]) -> dict[str, Any]:
        try:
            details = AccountCreate(name=name, email=email, password=password)
        except ValidationError as error:
            # do not include submitted passwords in the error message
            raise DemoAccountError("Invalid name, email or password") from error

        if role not in {"admin", "restaurant_user"}:
            raise DemoAccountError("Staff role must be admin or restaurant_user")

        if role == "admin" and restaurant_ids:
            raise DemoAccountError("Admins do not need restaurant assignments")

        for restaurant_id in restaurant_ids:
            if type(restaurant_id) is not int or restaurant_id <= 0:
                raise DemoAccountError("Restaurant IDs must be positive integers")
            if self.restaurants.get_by_id(restaurant_id) is None:
                raise DemoAccountError(f"Restaurant {restaurant_id} not found")

        password_hash = self.passwords.hash(details.password)

        try:
            return self.accounts.create_staff(
                details.name, details.email, password_hash, role, restaurant_ids)
        except AccountEmailExistsError as error:
            raise AccountExistsError("Email already in use") from error
