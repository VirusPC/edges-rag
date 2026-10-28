from __future__ import annotations

import hmac

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials


def verify_bearer(
    credentials: HTTPAuthorizationCredentials | None,
    expected: str,
) -> None:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized
    presented = credentials.credentials.encode("utf-8")
    required = expected.encode("utf-8")
    if not hmac.compare_digest(presented, required):
        raise unauthorized
