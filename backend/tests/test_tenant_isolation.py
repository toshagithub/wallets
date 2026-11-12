from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient
from psycopg import Connection
from psycopg.errors import InsufficientPrivilege
from app.auth.jwt import create_access_token
from app.db.dependencies import get_tenant_connection


app = FastAPI()


@app.get("/test/programs")
def get_programs(
    connection: Connection = Depends(get_tenant_connection),
):
    rows = connection.execute(
        """
        SELECT id, tenant_id, name
        FROM program
        ORDER BY id
        """
    ).fetchall()

    return [
        {
            "id": row[0],
            "tenant_id": row[1],
            "name": row[2],
        }
        for row in rows
    ]


@app.post("/test/programs/{program_id}")
def create_program(
    program_id: int,
    connection: Connection = Depends(get_tenant_connection),
):
    try:
        connection.execute(
            """
            INSERT INTO program (id, tenant_id, name, created_at)
            VALUES (%s, 1002, 'Unauthorized program', CURRENT_TIMESTAMP)
            """,
            (program_id,),
        )
    except InsufficientPrivilege:
        raise HTTPException(
            status_code=403,
            detail="Tenant isolation policy denied the operation",
        )

    return {"status": "created"}


@app.put("/test/programs/{program_id}")
def update_program(
    program_id: int,
    connection: Connection = Depends(get_tenant_connection),
):
    cursor = connection.execute(
        """
        UPDATE program
        SET name = 'Unauthorized update'
        WHERE id = %s
        """,
        (program_id,),
    )

    return {"rowcount": cursor.rowcount}


@app.delete("/test/programs/{program_id}")
def delete_program(
    program_id: int,
    connection: Connection = Depends(get_tenant_connection),
):
    cursor = connection.execute(
        """
        DELETE FROM program
        WHERE id = %s
        """,
        (program_id,),
    )

    return {"rowcount": cursor.rowcount}


client = TestClient(app)
def tenant_headers(tenant_id: int) -> dict[str, str]:
    token = create_access_token(user_id=1, tenant_id=tenant_id)
    return {
        "X-Tenant-ID": str(tenant_id),
        "Authorization": f"Bearer {token}",
    }


def test_tenant_isolation():
    # Tenant 1001 vidi samo svoje podatke.
    response_1 = client.get(
        "/test/programs",
        headers=tenant_headers(1001),
    )

    assert response_1.status_code == 200
    assert response_1.json() == [
        {
            "id": 1001,
            "tenant_id": 1001,
            "name": "Program Tenant 1",
        }
    ]

    # Tenant 1002 vidi samo svoje podatke.
    response_2 = client.get(
        "/test/programs",
        headers=tenant_headers(1002),
    )

    assert response_2.status_code == 200
    programs = response_2.json()

    assert programs
    assert all(row["tenant_id"] == 1002 for row in programs)
    assert any(row["id"] == 1002 for row in programs)

def test_tenant_cannot_insert_for_another_tenant():
    response = client.post(
        "/test/programs/1003",
        headers=tenant_headers(1001),
    )

    assert response.status_code == 403


def test_tenant_cannot_update_another_tenant():
    response = client.put(
        "/test/programs/1002",
        headers=tenant_headers(1001),
    )

    assert response.status_code == 200
    assert response.json() == {"rowcount": 0}


def test_tenant_cannot_delete_another_tenant():
    response = client.delete(
        "/test/programs/1002",
        headers=tenant_headers(1001),
    )

    assert response.status_code == 200
    assert response.json() == {"rowcount": 0}
