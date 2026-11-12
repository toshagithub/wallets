from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException

from app.config.settings import settings


ALGORITHM = "HS256"


def create_access_token(user_id: int, tenant_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "tenant_id": tenant_id,
        "exp": expires_at,
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=401,
            detail="Token je istekao",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=401,
            detail="Neispravan token",
        ) from exc

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")

    if user_id is None or tenant_id is None:
        raise HTTPException(
            status_code=401,
            detail="Token nema potrebne podatke",
        )

    try:
        return {
            "user_id": int(user_id),
            "tenant_id": int(tenant_id),
        }
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=401,
            detail="Neispravni podaci u tokenu",
        ) from exc
