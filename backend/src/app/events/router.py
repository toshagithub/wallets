from datetime import date, datetime, time, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from psycopg import Connection

from app.db.dependencies import get_tenant_connection
from app.utils.datetime import belgrade_to_utc


router = APIRouter(prefix="/events", tags=["events"])


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    event_date: date
    event_time: time
    ends_at: Optional[datetime] = None
    location: Optional[str] = Field(default=None, max_length=500)
    capacity: Optional[int] = Field(default=None, gt=0)
    description: Optional[str] = None
    image_url: Optional[str] = Field(default=None, max_length=2000)


class EventEndUpdate(BaseModel):
    ends_at: datetime


class EventResponse(BaseModel):
    id: int
    name: str
    event_date: Optional[date] = None
    event_time: Optional[time] = None
    ends_at: Optional[datetime] = None
    location: Optional[str] = None
    capacity: Optional[int] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime


def event_to_dict(row: tuple) -> dict:
    return {
        "id": row[0],
        "name": row[1],
        "event_date": row[2],
        "event_time": row[3],
        "ends_at": row[4],
        "location": row[5],
        "capacity": row[6],
        "description": row[7],
        "image_url": row[8],
        "created_at": row[9],
    }


def normalize_event_datetimes(
    event_date: date,
    event_time: time,
    ends_at: datetime,
) -> tuple[datetime, datetime]:
    starts_local = datetime.combine(event_date, event_time)

    try:
        starts_utc = belgrade_to_utc(starts_local)
        ends_utc = (
            belgrade_to_utc(ends_at)
            if ends_at.tzinfo is None
            else ends_at.astimezone(timezone.utc)
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    return starts_utc, ends_utc


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    data: EventCreate,
    connection: Connection = Depends(get_tenant_connection),
) -> dict:
    name = data.name.strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Naziv događaja ne može biti prazan",
        )

    ends_at_utc = None

    if data.ends_at is not None:
        starts_at_utc, ends_at_utc = normalize_event_datetimes(
            data.event_date,
            data.event_time,
            data.ends_at,
        )

        if ends_at_utc <= starts_at_utc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Završetak događaja mora biti posle početka",
            )

    row = connection.execute(
        """
        INSERT INTO program (
            tenant_id, name, created_at, event_date, event_time, ends_at,
            location, capacity, description, image_url
        )
        VALUES (
            current_setting('app.tenant_id')::BIGINT, %s, CURRENT_TIMESTAMP,
            %s, %s, %s, %s, %s, %s, %s
        )
        RETURNING id, name, event_date, event_time, ends_at, location,
                  capacity, description, image_url, created_at
        """,
        (
            name,
            data.event_date,
            data.event_time,
            ends_at_utc,
            data.location,
            data.capacity,
            data.description,
            data.image_url,
        ),
    ).fetchone()

    return event_to_dict(row)


@router.patch("/{event_id}/end-time", response_model=EventResponse)
def update_event_end_time(
    event_id: int,
    data: EventEndUpdate,
    connection: Connection = Depends(get_tenant_connection),
) -> dict:
    event = connection.execute(
        """
        SELECT id, name, event_date, event_time
        FROM program
        WHERE id = %s
          AND tenant_id = current_setting('app.tenant_id')::BIGINT
        """,
        (event_id,),
    ).fetchone()

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Događaj nije pronađen.",
        )

    if event[2] is None or event[3] is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Događaj mora imati datum i vreme početka.",
        )

    starts_at_utc, ends_at_utc = normalize_event_datetimes(
        event[2],
        event[3],
        data.ends_at,
    )

    if ends_at_utc <= starts_at_utc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Završetak događaja mora biti posle početka.",
        )

    row = connection.execute(
        """
        UPDATE program
        SET ends_at = %s
        WHERE id = %s
          AND tenant_id = current_setting('app.tenant_id')::BIGINT
        RETURNING id, name, event_date, event_time, ends_at, location,
                  capacity, description, image_url, created_at
        """,
        (ends_at_utc, event_id),
    ).fetchone()

    return event_to_dict(row)


@router.get("", response_model=list[EventResponse])
def list_events(
    connection: Connection = Depends(get_tenant_connection),
) -> list[dict]:
    rows = connection.execute(
        """
        SELECT id, name, event_date, event_time, ends_at, location,
               capacity, description, image_url, created_at
        FROM program
        ORDER BY event_date NULLS LAST, event_time NULLS LAST, id
        """
    ).fetchall()

    return [event_to_dict(row) for row in rows]
