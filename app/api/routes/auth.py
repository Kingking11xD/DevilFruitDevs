from fastapi import APIRouter, HTTPException

from app.api.dependencies import account_service
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.account_service import InactiveAccountError, InvalidCredentialsError
from app.services.token_service import create_access_token

router = APIRouter()


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Sign in",
    description="Check account credentials and return a random session token valid for 30 minutes.",
    responses={
        401: {"description": "Invalid email or password"},
        403: {"description": "Account is inactive"},
        422: {"description": "Invalid sign-in fields"},
        500: {"description": "Sign-in is unavailable"}})
def sign_in(data: LoginRequest) -> TokenResponse:
    try:
        account = account_service.authenticate(data.email, data.password)
        return TokenResponse(access_token=create_access_token(account["id"]))
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=401, detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}) from error
    except InactiveAccountError as error:
        raise HTTPException(status_code=403, detail="Account is inactive") from error
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=500, detail="Sign-in is unavailable") from error
