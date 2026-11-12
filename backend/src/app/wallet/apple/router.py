import json
from pathlib import Path

from app.wallet.apple.event_ticket_generator import generate_apple_event_ticket
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from psycopg import Connection

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_tenant_connection
from app.wallet.apple.generator import generate_apple_pass
from app.wallet.serial_number import generate_serial_number


router = APIRouter(
    prefix="/wallet/apple",
    tags=["apple-wallet"],
)


@router.post("/pass")
def generate_pass(
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_tenant_connection),
) -> Response:
    tenant_id = current_user["tenant_id"]

    serial_number = generate_serial_number(connection, tenant_id)

    member_name = f"Korisnik {current_user['user_id']}"
    member_number = f"KP{current_user['user_id']:03d}"
    status = "Aktivno"

    pass_data = generate_apple_pass(
        member_name=member_name,
        member_number=member_number,
        status=status,
        serial_number=serial_number,
	tenant_id=tenant_id,
    )

    return Response(
        content=pass_data,
        media_type="application/vnd.apple.pkpass",
        headers={
            "Content-Disposition": 'attachment; filename="wallet-pass.pkpass"',
        },
    )

@router.post("/event-pass")
def generate_event_pass(
    current_user: dict = Depends(get_current_user),
) -> Response:
    example_path = (
        Path(__file__).resolve().parents[1]
        / "canonical"
        / "example.json"
    )

    with example_path.open(encoding="utf-8") as file:
        canonical_data = json.load(file)

    pass_data = generate_apple_event_ticket(canonical_data)

    return Response(
        content=pass_data,
        media_type="application/vnd.apple.pkpass",
        headers={
            "Content-Disposition": 'attachment; filename="event-ticket.pkpass"',
        },
    )
