from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from psycopg import Connection

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_tenant_connection
from app.wallet.qr import verify_signed_qr_content


router = APIRouter(prefix="/scanner", tags=["scanner"])


ScanResult = Literal[
    "VAŽI",
    "NE POSTOJI",
    "VEĆ OČITANA",
    "ISTEKLA",
    "PONIŠTENA",
]


class ScanRequest(BaseModel):
    qr_content: str = Field(min_length=1, max_length=2048)
    device_registration_id: int = Field(gt=0)


class ScanResponse(BaseModel):
    result: ScanResult
    message: str
    scanned_at: datetime


def _record_scan(
    connection: Connection,
    *,
    tenant_id: int,
    pass_id: int | None,
    device_registration_id: int,
    user_id: int,
    result: ScanResult,
) -> datetime:
    row = connection.execute(
        """
        INSERT INTO skeniranje (
            tenant_id,
            pass_id,
            device_registration_id,
            user_id,
            result,
            method,
            scanned_at
        )
        VALUES (%s, %s, %s, %s, %s, 'QR', CURRENT_TIMESTAMP)
        RETURNING scanned_at
        """,
        (
            tenant_id,
            pass_id,
            device_registration_id,
            user_id,
            result,
        ),
    ).fetchone()

    return row[0]


def _response(
    connection: Connection,
    *,
    tenant_id: int,
    pass_id: int | None,
    device_registration_id: int,
    user_id: int,
    result: ScanResult,
) -> ScanResponse:
    messages = {
        "VAŽI": "Ulaznica je prihvaćena.",
        "NE POSTOJI": "Ulaznica nije pronađena ili QR kod nije validan.",
        "VEĆ OČITANA": "Ulaznica je već očitana.",
        "ISTEKLA": "Ulaznica nije u periodu važenja.",
        "PONIŠTENA": "Ulaznica je poništena.",
    }

    scanned_at = _record_scan(
        connection,
        tenant_id=tenant_id,
        pass_id=pass_id,
        device_registration_id=device_registration_id,
        user_id=user_id,
        result=result,
    )

    return ScanResponse(
        result=result,
        message=messages[result],
        scanned_at=scanned_at,
    )


@router.post("/scan", response_model=ScanResponse)
def scan_qr(
    data: ScanRequest,
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_tenant_connection),
):
    tenant_id = current_user["tenant_id"]
    user_id = current_user["user_id"]

    device = connection.execute(
        """
        SELECT id
        FROM registracija_uredjaja
        WHERE id = %s
          AND tenant_id = %s
          AND revoked_at IS NULL
        """,
        (data.device_registration_id, tenant_id),
    ).fetchone()

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Uređaj nije registrovan ili mu je pristup opozvan.",
        )

    # QR potpis se proverava pre nego što se podaci koriste za pronalaženje ulaznice.
    if not verify_signed_qr_content(data.qr_content):
        return _response(
            connection,
            tenant_id=tenant_id,
            pass_id=None,
            device_registration_id=device[0],
            user_id=user_id,
            result="NE POSTOJI",
        )

    parts = data.qr_content.split("|")
    _, qr_tenant_id, serial_number, _ = parts

    # Tenant iz potpisanog QR-a mora odgovarati prijavljenom korisniku.
    if int(qr_tenant_id) != tenant_id:
        return _response(
            connection,
            tenant_id=tenant_id,
            pass_id=None,
            device_registration_id=device[0],
            user_id=user_id,
            result="NE POSTOJI",
        )

    # FOR UPDATE zaključava red dok se ne završi transakcija, sprečavajući
    # da dva paralelna skeniranja prihvate istu ulaznicu.
    ticket = connection.execute(
        """
        SELECT id, status, valid_from, valid_until
        FROM pass
        WHERE tenant_id = %s
          AND serial_number = %s
        FOR UPDATE
        """,
        (tenant_id, serial_number),
    ).fetchone()

    if ticket is None:
        return _response(
            connection,
            tenant_id=tenant_id,
            pass_id=None,
            device_registration_id=device[0],
            user_id=user_id,
            result="NE POSTOJI",
        )
    pass_id, pass_status, valid_from, valid_until = ticket
    if pass_status == "poništen":
        result: ScanResult = "PONIŠTENA"
    elif pass_status == "skeniran":
        result = "VEĆ OČITANA"
    elif pass_status not in ("poslat", "otvoren", "instaliran", "uklonjen"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Došlo je do interne greške pri obradi ulaznice.",
        )
    else:
        now = datetime.now(timezone.utc)

        if valid_from is not None:
            if valid_from.tzinfo is None:
                valid_from = valid_from.replace(tzinfo=timezone.utc)

        if valid_until is not None:
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=timezone.utc)

        if valid_from is not None and now < valid_from:
            result = "ISTEKLA"
        elif valid_until is not None and now > valid_until:
            result = "ISTEKLA"
        else:
            updated = connection.execute(
                """
                UPDATE pass
                SET status = 'skeniran'
                WHERE id = %s
                  AND tenant_id = %s
                  AND status IN ('poslat', 'otvoren', 'instaliran', 'uklonjen')
                RETURNING id
                """,
                (pass_id, tenant_id),
            ).fetchone()

            result = "VAŽI" if updated is not None else "VEĆ OČITANA"

    return _response(
        connection,
        tenant_id=tenant_id,
        pass_id=pass_id,
        device_registration_id=device[0],
        user_id=user_id,
        result=result,
    )
