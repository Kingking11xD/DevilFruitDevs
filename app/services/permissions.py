from typing import Any

from app.services.account_service import InactiveAccountError


class PermissionDeniedError(Exception):
    pass


class ResourceNotFoundError(Exception):
    pass


def require_role(account: dict[str, Any], allowed_roles: set[str]) -> None:
    if not account["active"]:
        raise InactiveAccountError("Account is inactive")

    if account["role"] not in allowed_roles:
        raise PermissionDeniedError("Account role is not allowed")


def require_owner(account: dict[str, Any], customer_id: int) -> None:
    require_role(account, {"customer"})

    if account["id"] != customer_id:
        # do not reveal another customer's private cart or order
        raise ResourceNotFoundError("Resource not found")


def require_restaurant_access(account: dict[str, Any], restaurant_id: int) -> None:
    require_role(account, {"admin", "restaurant_user"})

    if account["role"] == "admin":
        return

    if restaurant_id not in account["managed_restaurant_ids"]:
        raise PermissionDeniedError("Restaurant access is not allowed")
