from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.account import Account


class AuthAccount(Account):
    managed_restaurant_ids: list[int] = Field(default_factory=list)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(repr=False)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int = 1800
