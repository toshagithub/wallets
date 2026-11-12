from datetime import date, datetime, time, timezone
import json
import secrets
from io import BytesIO
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from psycopg import Connection

from app.auth.dependencies import get_current_user
from app.db.dependencies import get_tenant_connection
from app.utils.datetime import belgrade_to_utc, utc_to_belgrade
from app.services.email import send_pass_email
from app.services.pass_email_content import (
    build_apple_pass_email,
    build_both_pass_email,
    build_google_pass_email,
)
from app.wallet.apple.event_ticket_generator import generate_apple_event_ticket
from app.wallet.google.generator import generate_google_event_ticket_pass
from app.wallet.qr import generate_signed_qr_content
from app.wallet.serial_number import generate_serial_number


router = APIRouter(prefix="/passes", tags=["passes"])


class IssuePassRequest(BaseModel):
    program_id: int = Field(gt=0)
    ticket_type_id: int = Field(gt=0)
    guest_ids: list[int] = Field(min_length=1, max_length=200)
    platform: Literal["apple", "google", "both"]

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        result = super().model_validate(obj, *args, **kwargs)
        if len(result.guest_ids) != len(set(result.guest_ids)):
            raise ValueError("Lista gostiju sadrži duplikate.")
        return result


def _iso_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _build_canonical_data(
    connection: Connection,
    tenant_id: int,
    pass_id: int,
    serial_number: str,
    program_id: int,
    ticket_type_id: int,
    guest_id: int,
) -> dict:
    event = connection.execute(
        """
        SELECT p.name, p.event_date, p.event_time, p.ends_at, p.location,
               t.name, t.price, t.currency, t.id,
               tenant.name, tenant.id
        FROM program p
        JOIN tip_karte t ON t.program_id = p.id
        JOIN public.tenant tenant ON tenant.id = p.tenant_id
        WHERE p.id = %s AND t.id = %s
          AND p.tenant_id = %s AND t.tenant_id = %s
        """,
        (program_id, ticket_type_id, tenant_id, tenant_id),
    ).fetchone()

    guest = connection.execute(
        """
        SELECT id, name, email, phone
        FROM primalac
        WHERE id = %s AND program_id = %s AND tenant_id = %s
        """,
        (guest_id, program_id, tenant_id),
    ).fetchone()

    if event is None or guest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Događaj, tip ulaznice ili gost nije pronađen.",
        )

    event_name, event_date, event_time, ends_at, location = event[:5]
    ticket_name, ticket_price, currency = event[5:8]
    tenant_name, resolved_tenant_id = event[9:11]

    if event_date is None or event_time is None or ends_at is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Događaju moraju biti podešeni početak i završetak pre izdavanja ulaznica.",
        )

    try:
        starts_at_utc = belgrade_to_utc(
            datetime.combine(event_date, event_time)
        )

        if ends_at.tzinfo is None:
            raise ValueError("Vreme završetka nema definisanu vremensku zonu.")

        ends_at_utc = ends_at.astimezone(timezone.utc)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    if ends_at_utc <= starts_at_utc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Završetak događaja mora biti posle početka.",
        )

    return {
        "pass": {"id": pass_id, "serial_number": serial_number},
        "tenant": {"id": resolved_tenant_id, "name": tenant_name},
        "event": {
            "id": program_id,
            "name": event_name,
            "starts_at": utc_to_belgrade(starts_at_utc).isoformat(),
            "ends_at": utc_to_belgrade(ends_at_utc).isoformat(),
            "location": location or "",
        },
        "holder": {
            "id": guest[0],
            "name": guest[1],
            **({"email": guest[2]} if guest[2] is not None else {}),
            **({"phone": guest[3]} if guest[3] is not None else {}),
        },
        "ticket_type": {
            "id": ticket_type_id,
            "name": ticket_name,
            "description": f"{ticket_price} {currency}",
        },
        "visual": {
            "logo_text": tenant_name,
            "foreground_color": "#000000",
            "background_color": "#FFFFFF",
        },
        "meta": {"schema_version": "1.0"},
    }


@router.post("/issue")
def issue_passes(
    data: IssuePassRequest,
    current_user: dict = Depends(get_current_user),
    connection: Connection = Depends(get_tenant_connection),
):
    tenant_id = current_user["tenant_id"]
    guest_ids = set(data.guest_ids)

    if len(guest_ids) != len(data.guest_ids):
        raise HTTPException(status_code=422, detail="Lista gostiju sadrži duplikate.")

    platforms = ["apple", "google"] if data.platform == "both" else [data.platform]

    event = connection.execute(
        """
        SELECT id, capacity, ends_at
        FROM program
        WHERE id = %s AND tenant_id = %s
        FOR UPDATE
        """,
        (data.program_id, tenant_id),
    ).fetchone()
    if event is None:
        raise HTTPException(status_code=404, detail="Događaj nije pronađen.")

    ticket_type = connection.execute(
        """
        SELECT id, quantity_limit
        FROM tip_karte
        WHERE id = %s AND program_id = %s AND tenant_id = %s
        """,
        (data.ticket_type_id, data.program_id, tenant_id),
    ).fetchone()
    if ticket_type is None:
        raise HTTPException(status_code=404, detail="Tip ulaznice nije pronađen.")

    found_guest_ids = {
        row[0]
        for row in connection.execute(
            """
            SELECT id FROM primalac
            WHERE program_id = %s AND tenant_id = %s AND id = ANY(%s)
            """,
            (data.program_id, tenant_id, data.guest_ids),
        ).fetchall()
    }
    if found_guest_ids != guest_ids:
        raise HTTPException(
            status_code=422,
            detail="Jedan ili više gostiju ne pripada izabranom događaju.",
        )

    existing_passes = connection.execute(
        """
        SELECT recipient_id, id, serial_number
        FROM pass
        WHERE tenant_id = %s
          AND ticket_type_id = %s
          AND recipient_id = ANY(%s)
          AND status <> 'poništen'
        """,
        (tenant_id, data.ticket_type_id, data.guest_ids),
    ).fetchall()
    existing_by_guest = {row[0]: (row[1], row[2]) for row in existing_passes}

    if existing_by_guest and set(existing_by_guest) != guest_ids:
        raise HTTPException(
            status_code=409,
            detail="Neki izabrani gosti već imaju ulaznicu, a neki nemaju. Izaberite goste sa istim stanjem ulaznica.",
        )

    new_pass_count = 0 if existing_by_guest else len(guest_ids)

    if event[1] is not None and new_pass_count:
        total_issued_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM pass p
            JOIN tip_karte t ON t.id = p.ticket_type_id
            WHERE p.tenant_id = %s
              AND t.program_id = %s
              AND p.status <> 'poništen'
            """,
            (tenant_id, data.program_id),
        ).fetchone()[0]

        if total_issued_count + new_pass_count > event[1]:
            raise HTTPException(
                status_code=409,
                detail="Dostignut je kapacitet događaja.",
            )

    if ticket_type[1] is not None and not existing_by_guest:
        issued_count = connection.execute(
            """
            SELECT COUNT(*) FROM pass
            WHERE tenant_id = %s AND ticket_type_id = %s
              AND status <> 'poništen'
            """,
            (tenant_id, data.ticket_type_id),
        ).fetchone()[0]
        if issued_count + len(data.guest_ids) > ticket_type[1]:
            raise HTTPException(
                status_code=409,
                detail="Nema dovoljno raspoloživih ulaznica ovog tipa.",
            )

    issued = []
    email_tasks = []
    apple_archive = BytesIO()

    for guest_id in data.guest_ids:
        if guest_id in existing_by_guest:
            pass_id, serial_number = existing_by_guest[guest_id]
        else:
            serial_number = generate_serial_number(connection, tenant_id)
            row = connection.execute(
                """
                INSERT INTO pass (
                    tenant_id, ticket_type_id, recipient_id, serial_number,
                    status, issued_at, valid_from, valid_until, created_at
                )
                VALUES (
                    %s, %s, %s, %s, 'poslat', CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP, %s, CURRENT_TIMESTAMP
                )
                RETURNING id
                """,
                (
                    tenant_id,
                    data.ticket_type_id,
                    guest_id,
                    serial_number,
                    event[2],
                ),
            ).fetchone()
            pass_id = row[0]

        for platform in platforms:
            platform_record = connection.execute(
                """
                SELECT id FROM pass_platform_issuance
                WHERE tenant_id = %s AND pass_id = %s AND platform = %s
                """,
                (tenant_id, pass_id, platform),
            ).fetchone()

            if platform_record is not None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Gost sa ID {guest_id} već ima evidentiranu {platform.capitalize()} ulaznicu.",
                )

        canonical_data = _build_canonical_data(
            connection=connection,
            tenant_id=tenant_id,
            pass_id=pass_id,
            serial_number=serial_number,
            program_id=data.program_id,
            ticket_type_id=data.ticket_type_id,
            guest_id=guest_id,
        )

        pkpass = None
        save_url = None

        if "apple" in platforms:
            token_row = connection.execute(
                """
                SELECT apple_authentication_token
                FROM public.pass
                WHERE id = %s AND tenant_id = %s
                """,
                (pass_id, tenant_id),
            ).fetchone()

            authentication_token = token_row[0]

            if authentication_token is None:
                authentication_token = secrets.token_urlsafe(32)

                connection.execute(
                    """
                    UPDATE public.pass
                    SET apple_authentication_token = %s
                    WHERE id = %s AND tenant_id = %s
                    """,
                    (authentication_token, pass_id, tenant_id),
                )

            pkpass = generate_apple_event_ticket(
                canonical_data,
                authentication_token,
            )

            if data.platform == "apple":
                with ZipFile(apple_archive, mode="a", compression=ZIP_DEFLATED) as archive:
                    archive.writestr(f"{serial_number}.pkpass", pkpass)

        if "google" in platforms:
            save_url = generate_google_event_ticket_pass(canonical_data)

        for platform in platforms:
            connection.execute(
                """
                INSERT INTO pass_platform_issuance (tenant_id, pass_id, platform)
                VALUES (%s, %s, %s)
                """,
                (tenant_id, pass_id, platform),
            )

        email_tasks.append({
            "recipient": canonical_data["holder"].get("email"),
            "canonical_data": canonical_data,
            "attachment_bytes": pkpass,
            "attachment_filename": f"{serial_number}.pkpass" if pkpass else None,
            "save_url": save_url,
        })

        issued_item = {
            "guest_id": guest_id,
            "pass_id": pass_id,
            "serial_number": serial_number,
        }
        if save_url:
            issued_item["save_url"] = save_url

        issued.append(issued_item)

    # Potvrđujemo izdavanje pre pokušaja slanja emailova.
    connection.commit()

    email_results = {
        "sent": 0,
        "failed": 0,
        "skipped": 0,
    }

    for task in email_tasks:
        recipient = task["recipient"]

        if not recipient:
            email_results["skipped"] += 1
            continue

        try:
            if data.platform == "apple":
                email_content = build_apple_pass_email(
                    task["canonical_data"]
                )
            elif data.platform == "google":
                email_content = build_google_pass_email(
                    task["canonical_data"],
                    task["save_url"],
                )
            else:
                email_content = build_both_pass_email(
                    task["canonical_data"],
                    task["save_url"],
                )

            send_pass_email(
                recipient=recipient,
                subject=email_content["subject"],
                text_body=email_content["text_body"],
                html_body=email_content["html_body"],
                attachment_bytes=task["attachment_bytes"],
                attachment_filename=task["attachment_filename"],
            )

            email_results["sent"] += 1

        except Exception:
            email_results["failed"] += 1

    if data.platform == "apple":
        apple_archive.seek(0)
        return StreamingResponse(
            apple_archive,
            media_type="application/zip",
            headers={
                "Content-Disposition": 'attachment; filename="apple_passes.zip"',
                "X-Email-Results": json.dumps(email_results),
            },
        )

    return {
        "issued": issued,
        "count": len(issued),
        "email_results": email_results,
    }
