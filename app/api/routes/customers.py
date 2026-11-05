from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import account_service as service, get_current_customer
from app.schemas.account import Account, AccountCreate, AccountUpdate, AddressUpdate
from app.services.account_service import (
    AccountExistsError, InactiveAccountError, InvalidCredentialsError)

router = APIRouter()

repository = service.repository


def account_update_error(error: Exception) -> HTTPException:
    if isinstance(error, InvalidCredentialsError):
        return HTTPException(
            status_code=401, detail="Invalid authentication",
            headers={"WWW-Authenticate": "Bearer"})

    if isinstance(error, InactiveAccountError):
        return HTTPException(status_code=403, detail="Account is inactive")

    return HTTPException(status_code=500, detail="Account could not be saved")


@router.post(
    "/customers",
    response_model=Account,
    status_code=201,
    summary="Register a customer",
    description="Create a customer account with a unique ID and a hashed password.",
    responses={
        409: {"description": "Email already in use"},
        422: {"description": "Invalid account information"},
        500: {"description": "Account could not be saved"}})
def register_customer(data: AccountCreate) -> Account:
    try:
        account = service.register_customer(data.name, data.email, data.password)
        return Account.model_validate(account)
    except AccountExistsError as error:
        raise HTTPException(status_code=409, detail="Email already in use") from error
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Account could not be saved") from error


@router.get("/customers/me", response_model=Account, summary="View my profile")
def get_profile(
        account: Annotated[dict[str, Any], Depends(get_current_customer)]) -> Account:
    return Account.model_validate(account)


@router.patch("/customers/me", response_model=Account, summary="Update my name")
def update_profile(
        data: AccountUpdate,
        account: Annotated[dict[str, Any], Depends(get_current_customer)]) -> Account:
    try:
        updated = service.update_name(account["id"], data.name)
        return Account.model_validate(updated)
    except (InvalidCredentialsError, InactiveAccountError, OSError, ValueError) as error:
        raise account_update_error(error) from error


@router.patch("/customers/me/address", response_model=Account, summary="Update my address")
def update_address(
        data: AddressUpdate,
        account: Annotated[dict[str, Any], Depends(get_current_customer)]) -> Account:
    try:
        updated = service.update_address(account["id"], data.delivery_address)
        return Account.model_validate(updated)
    except (InvalidCredentialsError, InactiveAccountError, OSError, ValueError) as error:
        raise account_update_error(error) from error


@router.post("/customers/me/deactivate", response_model=Account, summary="Deactivate my account")
def deactivate_account(
        account: Annotated[dict[str, Any], Depends(get_current_customer)]) -> Account:
    try:
        updated = service.deactivate(account["id"])
        return Account.model_validate(updated)
    except (InvalidCredentialsError, InactiveAccountError, OSError, ValueError) as error:
        raise account_update_error(error) from error
