import secrets
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

from app.services.account_service import InvalidCredentialsError


sessions: dict[str, dict[str, Any]] = {}
session_lock = Lock()


def _remove_expired_sessions(now: datetime) -> None:
    for token, session in list(sessions.items()):
        if session["expires_at"] <= now:
            del sessions[token]


def create_access_token(account_id: int) -> str:
    now = datetime.now(timezone.utc)

    # requests can run at the same time so protect changes to the sessions
    with session_lock:
        _remove_expired_sessions(now)

        token = secrets.token_urlsafe(32)
        sessions[token] = {
            "account_id": account_id,
            "expires_at": now + timedelta(minutes=30)}
        return token


def read_account_id(token: str) -> int:
    with session_lock:
        _remove_expired_sessions(datetime.now(timezone.utc))
        session = sessions.get(token)
        if session is None:
            raise InvalidCredentialsError("Invalid authentication")

        return session["account_id"]
