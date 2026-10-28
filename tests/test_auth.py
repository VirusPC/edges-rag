import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from edges_rag.auth import verify_bearer


def test_verify_bearer_accepts_match():
    verify_bearer(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials="secret"),
        expected="secret",
    )


def test_verify_bearer_rejects_mismatch():
    with pytest.raises(HTTPException) as ei:
        verify_bearer(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials="nope"),
            expected="secret",
        )
    assert ei.value.status_code == 401


def test_verify_bearer_rejects_none():
    with pytest.raises(HTTPException) as ei:
        verify_bearer(None, expected="secret")
    assert ei.value.status_code == 401
