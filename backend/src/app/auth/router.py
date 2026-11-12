from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth.jwt import create_access_token
from app.auth.service import authenticate_user


router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(data: LoginRequest) -> dict:
    user = authenticate_user(data.email, data.password)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Neispravni email ili lozinka",
        )

    access_token = create_access_token(
        user_id=user["id"],
        tenant_id=user["tenant_id"],
    )

    return {
        "message": "Uspešna prijava",
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }
