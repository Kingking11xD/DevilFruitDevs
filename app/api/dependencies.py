from typing import Annotated, Any

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.repositories.account_repo import AccountRepo
from app.services.account_service import (
    AccountService, InactiveAccountError, InvalidCredentialsError)
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
