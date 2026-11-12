from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from psycopg import Connection

from app.db.dependencies import get_tenant_connection


router = APIRouter(prefix="/ticket-types", tags=["ticket-types"])


class TicketTypeCreate(BaseModel):
    program_id: int = Field(gt=0)
    name: str = Field(min_length=1, max_length=200)
    price: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    currency: str = Field(default="RSD", min_length=3, max_length=3)
    quantity_limit: Optional[int] = Field(default=None, gt=0)
    sale_start: Optional[datetime] = None
    sale_end: Optional[datetime] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Naziv tipa karte ne može biti prazan")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("Valuta mora biti troslovna oznaka, npr. RSD ili EUR")
        return value


class TicketTypeResponse(BaseModel):
    id: int
    program_id: int
    name: str
    price: Decimal
    currency: str
    quantity_limit: Optional[int] = None
    sale_start: Optional[datetime] = None
    sale_end: Optional[datetime] = None
    created_at: datetime


def ticket_type_to_dict(row: tuple) -> dict:
    return {
        "id": row[0],
        "program_id": row[1],
        "name": row[2],
        "price": row[3],
        "currency": row[4],
        "quantity_limit": row[5],
        "sale_start": row[6],
        "sale_end": row[7],
        "created_at": row[8],
    }


@router.post("", response_model=TicketTypeResponse, status_code=status.HTTP_201_CREATED)
def create_ticket_type(
    data: TicketTypeCreate,
    connection: Connection = Depends(get_tenant_connection),
) -> dict:
    if data.sale_start and data.sale_end and data.sale_end <= data.sale_start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Kraj prodaje mora biti posle početka prodaje",
        )

    event = connection.execute(
        "SELECT id FROM program WHERE id = %s",
        (data.program_id,),
    ).fetchone()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Događaj nije pronađen",
        )

    row = connection.execute(
        """
        INSERT INTO tip_karte (
            tenant_id, program_id, name, price, currency, quantity_limit,
            sale_start, sale_end, created_at
        )
        VALUES (
            current_setting('app.tenant_id')::BIGINT, %s, %s, %s, %s, %s,
            %s, %s, CURRENT_TIMESTAMP
        )
        RETURNING id, program_id, name, price, currency, quantity_limit,
                  sale_start, sale_end, created_at
        """,
        (
            data.program_id,
            data.name,
            data.price,
            data.currency,
            data.quantity_limit,
            data.sale_start,
            data.sale_end,
        ),
    ).fetchone()

    return ticket_type_to_dict(row)


@router.get("", response_model=list[TicketTypeResponse])
def list_ticket_types(
    program_id: int = 0,
    connection: Connection = Depends(get_tenant_connection),
) -> list[dict]:
    if program_id < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="ID događaja mora biti pozitivan",
        )

    if program_id:
        rows = connection.execute(
            """
            SELECT id, program_id, name, price, currency, quantity_limit,
                   sale_start, sale_end, created_at
            FROM tip_karte
            WHERE program_id = %s
            ORDER BY id
            """,
            (program_id,),
        ).fetchall()
    else:
        rows = connection.execute(
            """
            SELECT id, program_id, name, price, currency, quantity_limit,
                   sale_start, sale_end, created_at
            FROM tip_karte
            ORDER BY program_id, id
            """
        ).fetchall()

    return [ticket_type_to_dict(row) for row in rows]
