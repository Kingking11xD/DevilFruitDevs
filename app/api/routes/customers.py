from fastapi import APIRouter, HTTPException

from app.api.dependencies import account_service as service
from app.schemas.account import Account, AccountCreate
from app.services.account_service import AccountExistsError

router = APIRouter()

repository = service.repository


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
