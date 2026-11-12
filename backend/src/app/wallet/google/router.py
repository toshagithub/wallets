from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import Connection

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_tenant_connection
import json
from pathlib import Path

from app.wallet.google.generator import (
    generate_google_wallet_pass,
    generate_google_event_ticket_pass,
)
from app.wallet.serial_number import generate_serial_number


router = APIRouter(
    prefix="/wallet/google",
    tags=["google-wallet"],
)


class GoogleWalletPassResponse(BaseModel):
    save_url: str


@router.post("/pass", response_model=GoogleWalletPassResponse)
def generate_pass(
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_tenant_connection),
) -> GoogleWalletPassResponse:
    tenant_id = current_user["tenant_id"]

    try:
        serial_number = generate_serial_number(connection, tenant_id)
        save_url = generate_google_wallet_pass(
            tenant_id=tenant_id,
            serial_number=serial_number,
        )
        return GoogleWalletPassResponse(save_url=save_url)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Generisanje Google Wallet passa nije uspelo.",
        ) from error
@router.post("/event-pass", response_model=GoogleWalletPassResponse)
def generate_event_pass(
    current_user: dict = Depends(get_current_user),
) -> GoogleWalletPassResponse:
    example_path = (
        Path(__file__).resolve().parents[1]
        / "canonical"
        / "example.json"
    )

    try:
        with example_path.open(encoding="utf-8") as file:
            canonical_data = json.load(file)

        save_url = generate_google_event_ticket_pass(canonical_data)
        return GoogleWalletPassResponse(save_url=save_url)
    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail="Generisanje Google Wallet EventTicket passa nije uspelo.",
        ) from error
