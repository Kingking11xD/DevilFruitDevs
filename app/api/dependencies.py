from typing import Annotated, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositories.account_repo import AccountRepo
from app.services.account_service import (
    AccountService, InactiveAccountError, InvalidCredentialsError)
from app.services.permissions import (
    PermissionDeniedError, require_restaurant_access, require_role)
from app.services.token_service import read_account_id

repository = AccountRepo()
account_service = AccountService(repository)
bearer = HTTPBearer(auto_error=False)


def get_current_account(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=401, detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"})

    try:
        account_id = read_account_id(credentials.credentials)
        return account_service.get_active_account(account_id)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=401, detail="Invalid authentication",
            headers={"WWW-Authenticate": "Bearer"}) from error
    except InactiveAccountError as error:
        raise HTTPException(status_code=403, detail="Account is inactive") from error
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Authentication is unavailable") from error


def get_current_customer(
        account: Annotated[dict[str, Any], Depends(get_current_account)]) -> dict[str, Any]:
    try:
        require_role(account, {"customer"})
    except PermissionDeniedError as error:
        raise HTTPException(status_code=403, detail="Customer account required") from error

    return account


def get_current_admin(
        account: Annotated[dict[str, Any], Depends(get_current_account)]) -> dict[str, Any]:
    try:
        require_role(account, {"admin"})
    except PermissionDeniedError as error:
        raise HTTPException(status_code=403, detail="Administrator account required") from error

    return account


def get_restaurant_manager(
        restaurant_id: int,
        account: Annotated[dict[str, Any], Depends(get_current_account)]) -> dict[str, Any]:
    try:
        require_restaurant_access(account, restaurant_id)
    except PermissionDeniedError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error

    return account
