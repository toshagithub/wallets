from collections.abc import Generator

from fastapi import Depends, Header, HTTPException
from psycopg import Connection

from app.auth.dependencies import get_current_user
from app.db.connection import get_connection
from app.db.tenant import set_current_tenant


def get_tenant_connection(
    current_user: dict = Depends(get_current_user),
    x_tenant_id: int = Header(...),
) -> Generator[Connection, None, None]:
    if x_tenant_id != current_user["tenant_id"]:
        raise HTTPException(
            status_code=403,
            detail="Tenant ID se ne poklapa sa tokenom",
        )

    set_current_tenant(x_tenant_id)
    yield from get_connection(x_tenant_id)
