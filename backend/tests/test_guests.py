
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.db.dependencies import get_tenant_connection
from app.main import app


client = TestClient(app)


def tenant_headers(tenant_id: int = 1001) -> dict[str, str]:
    token = create_access_token(user_id=1, tenant_id=tenant_id)
    return {
        "X-Tenant-ID": str(tenant_id),
        "Authorization": f"Bearer {token}",
    }


def override_connection(connection: MagicMock) -> None:
    def dependency():
        yield connection

    app.dependency_overrides[get_tenant_connection] = dependency


def test_create_guest():
    connection = MagicMock()
    connection.execute.return_value.fetchone.side_effect = [
        (1,),
        None,
        (10, 1, "Ana Petrović", "ana@example.com", "+381601234567"),
    ]
    override_connection(connection)

    try:
        response = client.post(
            "/guests",
            headers=tenant_headers(),
            json={
                "program_id": 1,
                "name": "Ana Petrović",
                "email": "ANA@example.com",
                "phone": "+381601234567",
            },
        )

        assert response.status_code == 201
        assert response.json()["name"] == "Ana Petrović"
        assert response.json()["email"] == "ana@example.com"
        assert response.json()["program_id"] == 1
        assert connection.execute.call_count == 3
    finally:
        app.dependency_overrides.clear()


def test_create_guest_rejects_duplicate_email():
    connection = MagicMock()
    connection.execute.return_value.fetchone.side_effect = [
        (1,),
        (10,),
    ]
    override_connection(connection)

    try:
        response = client.post(
            "/guests",
            headers=tenant_headers(),
            json={
                "program_id": 1,
                "name": "Ana Petrović",
                "email": "ana@example.com",
            },
        )

        assert response.status_code == 409
        assert "već postoji" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_create_guest_rejects_missing_event():
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = None
    override_connection(connection)

    try:
        response = client.post(
            "/guests",
            headers=tenant_headers(),
            json={
                "program_id": 999,
                "name": "Ana Petrović",
                "email": "ana@example.com",
            },
        )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_create_guest_requires_authentication():
    response = client.post(
        "/guests",
        json={
            "program_id": 1,
            "name": "Ana Petrović",
        },
    )

    assert response.status_code == 401


def test_list_guests():
    connection = MagicMock()
    connection.execute.return_value.fetchall.return_value = [
        (10, 1, "Ana Petrović", "ana@example.com", "+381601234567"),
    ]
    override_connection(connection)

    try:
        response = client.get(
            "/guests?program_id=1",
            headers=tenant_headers(),
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Ana Petrović"
        connection.execute.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_parse_csv_guest_file():
    from app.guests.router import parse_guest_file

    content = (
        "name,email,phone\n"
        "Ana Petrović,ana@example.com,+381601234567\n"
    ).encode("utf-8")

    rows = parse_guest_file("gosti.csv", content)

    assert len(rows) == 1
    assert rows[0]["name"] == "Ana Petrović"
    assert rows[0]["email"] == "ana@example.com"
    assert rows[0]["phone"] == "+381601234567"


def test_parse_xlsx_guest_file():
    import io

    from openpyxl import Workbook

    from app.guests.router import parse_guest_file

    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["name", "email", "phone"])
    sheet.append(["Ana Petrović", "ana@example.com", "+381601234567"])

    buffer = io.BytesIO()
    workbook.save(buffer)

    rows = parse_guest_file("gosti.xlsx", buffer.getvalue())

    assert len(rows) == 1
    assert rows[0]["name"] == "Ana Petrović"
    assert rows[0]["email"] == "ana@example.com"
    assert rows[0]["phone"] == "+381601234567"
