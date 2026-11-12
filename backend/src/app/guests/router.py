
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field, field_validator
from psycopg import Connection

from app.db.dependencies import get_tenant_connection
from fastapi import File, UploadFile

router = APIRouter(prefix="/guests", tags=["guests"])


class GuestCreate(BaseModel):
    program_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ime gosta ne može biti prazno")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        if isinstance(value, str):
            value = value.strip().lower()
            return value or None
        return value

    @field_validator("phone", mode="before")
    @classmethod
    def normalize_phone(cls, value):
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value


class GuestResponse(BaseModel):
    id: int
    program_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


def guest_to_dict(row: tuple) -> dict:
    return {
        "id": row[0],
        "program_id": row[1],
        "name": row[2],
        "email": row[3],
        "phone": row[4],
    }


@router.post(
    "",
    response_model=GuestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_guest(
    data: GuestCreate,
    connection: Connection = Depends(get_tenant_connection),
) -> dict:
    event = connection.execute(
        "SELECT id FROM program WHERE id = %s",
        (data.program_id,),
    ).fetchone()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Događaj nije pronađen",
        )

    if data.email:
        duplicate = connection.execute(
            """
            SELECT id FROM primalac
            WHERE program_id = %s AND lower(email) = %s
            LIMIT 1
            """,
            (data.program_id, data.email),
        ).fetchone()

        if duplicate is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Gost sa ovom e-mail adresom već postoji za ovaj događaj",
            )

    row = connection.execute(
        """
        INSERT INTO primalac (
            tenant_id, program_id, name, email, phone
        )
        VALUES (
            current_setting('app.tenant_id')::BIGINT, %s, %s, %s, %s
        )
        RETURNING id, program_id, name, email, phone
        """,
        (
            data.program_id,
            data.name,
            data.email,
            data.phone,
        ),
    ).fetchone()

    return guest_to_dict(row)


@router.get("", response_model=list[GuestResponse])
def list_guests(
    program_id: int = Query(gt=0),
    connection: Connection = Depends(get_tenant_connection),
) -> list[dict]:
    rows = connection.execute(
        """
        SELECT id, program_id, name, email, phone
        FROM primalac
        WHERE program_id = %s
        ORDER BY id
        """,
        (program_id,),
    ).fetchall()

    return [guest_to_dict(row) for row in rows]


import csv
import io
from openpyxl import load_workbook


def parse_guest_file(filename: str, content: bytes) -> list[dict]:
    suffix = filename.lower().rsplit(".", 1)[-1]

    if suffix == "csv":
        text = content.decode("utf-8-sig")
        text = "\n".join(line for line in text.splitlines() if line.strip())

        header = next(
            (line for line in text.splitlines() if line.strip()),
            "",
        )
        delimiter = max(
            [",", ";", "\t"],
            key=header.count,
        )

        reader = csv.DictReader(
            io.StringIO(text),
            delimiter=delimiter,
        )
        rows = list(reader)


    elif suffix == "xlsx":
        workbook = load_workbook(
            io.BytesIO(content),
            read_only=True,
            data_only=True,
        )
        try:
            sheet = workbook.active
            values = sheet.iter_rows(values_only=True)
            headers = next(values, None)

            if not headers:
                raise HTTPException(
                    status_code=422,
                    detail="Excel fajl nema zaglavlje.",
                )

            names = [
                str(value).strip().lower() if value is not None else ""
                for value in headers
            ]
            rows = [
                dict(zip(names, row))
                for row in values
                if any(value is not None for value in row)
            ]
        finally:
            workbook.close()

    else:
        raise HTTPException(
            status_code=422,
            detail="Podržani su samo CSV i XLSX fajlovi.",
        )

    if not rows:
        raise HTTPException(
            status_code=422,
            detail="Fajl ne sadrži goste.",
        )

    normalized = []
    for row in rows:
        item = {
            str(key).strip().lower(): (
                str(value).strip() if value is not None else ""
            )
            for key, value in row.items()
            if key is not None
        }

        name = item.get("name") or item.get("ime") or item.get("ime i prezime")
        email = item.get("email") or item.get("e-mail")
        phone = item.get("phone") or item.get("telefon")

        if not name:
            continue

        normalized.append({
            "name": name,
            "email": email or None,
            "phone": phone or None,
        })

    if not normalized:
        raise HTTPException(
            status_code=422,
            detail="Nema redova sa imenom gosta. Očekivane kolone su name/ime, email i phone/telefon.",
        )

    return normalized


@router.post("/import")
async def import_guests(
    program_id: int = Query(gt=0),
    file: UploadFile = File(...),
    connection: Connection = Depends(get_tenant_connection),
) -> dict:
    filename = file.filename or ""

    if not filename.lower().endswith((".csv", ".xlsx")):
        raise HTTPException(
            status_code=422,
            detail="Podržani su samo CSV i XLSX fajlovi.",
        )

    content = await file.read()

    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Fajl ne sme biti veći od 5 MB.",
        )

    event = connection.execute(
        "SELECT id FROM program WHERE id = %s",
        (program_id,),
    ).fetchone()

    if event is None:
        raise HTTPException(
            status_code=404,
            detail="Događaj nije pronađen.",
        )

    rows = parse_guest_file(filename, content)

    imported = 0
    duplicates = 0
    invalid = 0
    seen_emails = set()

    for guest in rows:
        email = guest["email"]
        if email:
            email = email.strip().lower()

            if email in seen_emails:
                duplicates += 1
                continue

            seen_emails.add(email)

            existing = connection.execute(
                """
                SELECT id FROM primalac
                WHERE program_id = %s AND lower(email) = %s
                LIMIT 1
                """,
                (program_id, email),
            ).fetchone()

            if existing is not None:
                duplicates += 1
                continue

        try:
            connection.execute(
                """
                INSERT INTO primalac (
                    tenant_id, program_id, name, email, phone
                )
                VALUES (
                    current_setting('app.tenant_id')::BIGINT,
                    %s, %s, %s, %s
                )
                """,
                (
                    program_id,
                    guest["name"],
                    email,
                    guest["phone"],
                ),
            )
            imported += 1
        except Exception:
            invalid += 1

    return {
        "imported": imported,
        "duplicates": duplicates,
        "invalid": invalid,
        "total": len(rows),
    }
