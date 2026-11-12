from datetime import datetime
from decimal import Decimal
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


def test_create_ticket_type():
    connection = MagicMock()
    connection.execute.return_value.fetchone.side_effect = [
        (1,),
        (
            1,
            1,
            "Standard",
            Decimal("1500.00"),
            "RSD",
            30,
            None,
            None,
            datetime(2026, 10, 21, 10, 0),
        ),
    ]
    override_connection(connection)

    try:
        response = client.post(
            "/ticket-types",
            headers=tenant_headers(),
            json={
                "program_id": 1,
                "name": "Standard",
                "price": "1500.00",
                "currency": "rsd",
                "quantity_limit": 30,
            },
        )

        assert response.status_code == 201
        assert response.json()["name"] == "Standard"
        assert response.json()["currency"] == "RSD"
        assert response.json()["quantity_limit"] == 30
        assert connection.execute.call_count == 2
    finally:
        app.dependency_overrides.clear()



def test_create_ticket_type_uses_default_price_and_currency():
    connection = MagicMock()
    connection.execute.return_value.fetchone.side_effect = [
        (1,),
        (
            2,
            1,
            "VIP",
            Decimal("0"),
            "RSD",
            None,
            None,
            None,
            datetime(2026, 11, 9, 10, 0),
        ),
    ]
    override_connection(connection)

    try:
        response = client.post(
            "/ticket-types",
            headers=tenant_headers(),
            json={
                "program_id": 1,
                "name": "VIP",
            },
        )

        assert response.status_code == 201
        assert response.json()["name"] == "VIP"
        assert response.json()["price"] == "0"
        assert response.json()["currency"] == "RSD"
        assert response.json()["quantity_limit"] is None
        assert connection.execute.call_count == 2
    finally:
        app.dependency_overrides.clear()

def test_create_ticket_type_rejects_negative_price():
    response = client.post(
        "/ticket-types",
        headers=tenant_headers(),
        json={
            "program_id": 1,
            "name": "Standard",
            "price": "-1.00",
            "currency": "RSD",
        },
    )

    assert response.status_code == 422


def test_create_ticket_type_requires_authentication():
    response = client.post(
        "/ticket-types",
        json={
            "program_id": 1,
            "name": "Standard",
            "price": "1500.00",
            "currency": "RSD",
        },
    )

    assert response.status_code == 401


def test_list_ticket_types():
    connection = MagicMock()
    connection.execute.return_value.fetchall.return_value = [
        (
            1,
            1,
            "Standard",
            Decimal("1500.00"),
            "RSD",
            30,
            None,
            None,
            datetime(2026, 10, 21, 10, 0),
        )
    ]
    override_connection(connection)

    try:
        response = client.get(
            "/ticket-types?program_id=1",
            headers=tenant_headers(),
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Standard"
        connection.execute.assert_called_once()
    finally:
        app.dependency_overrides.clear()
