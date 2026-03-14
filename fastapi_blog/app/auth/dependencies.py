from typing import Annotated

import jwt
from fastapi import Cookie, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

import models
from auth.jwt import decode_access_token
from database import get_db

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _resolve_token(
    bearer: str | None,
    cookie: str | None,
) -> str | None:
    return bearer or cookie


def get_current_user(
    request: Request,
    bearer_token: Annotated[str | None, Depends(_oauth2_scheme)],
    cookie_token: Annotated[str | None, Cookie(alias="access_token")] = None,
    db: Session = Depends(get_db),
) -> models.User:

    token = _resolve_token(bearer_token, cookie_token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User belonging to this token no longer exists.",
        )

    return user


def get_current_user_optional(
    request: Request,
    bearer_token: Annotated[str | None, Depends(_oauth2_scheme)],
    cookie_token: Annotated[str | None, Cookie(alias="access_token")] = None,
    db: Session = Depends(get_db),
) -> models.User | None:

    try:
        return get_current_user(request, bearer_token, cookie_token, db)
    except HTTPException:
        return None


CurrentUser = Annotated[models.User, Depends(get_current_user)]
OptionalCurrentUser = Annotated[models.User | None, Depends(get_current_user_optional)]
