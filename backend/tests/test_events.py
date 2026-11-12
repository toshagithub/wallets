
from datetime import date, datetime, time
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


def test_create_event():
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = (
        1,
        "Plavi cvet",
        date(2026, 11, 5),
        time(20, 0),
        None,
        "Plavi cvet",
        40,
        "Proslava",
        None,
        datetime(2026, 10, 21, 10, 0),
    )
    override_connection(connection)

    try:
        response = client.post(
            "/events",
            headers=tenant_headers(),
            json={
                "name": "Plavi cvet",
                "event_date": "2026-11-05",
                "event_time": "20:00:00",
                "location": "Plavi cvet",
                "capacity": 40,
                "description": "Proslava",
            },
        )

        assert response.status_code == 201
        assert response.json()["id"] == 1
        assert response.json()["name"] == "Plavi cvet"
        assert response.json()["capacity"] == 40
        connection.execute.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_create_event_rejects_non_positive_capacity():
    response = client.post(
        "/events",
        headers=tenant_headers(),
        json={
            "name": "Plavi cvet",
            "event_date": "2026-11-05",
            "event_time": "20:00:00",
            "capacity": 0,
        },
    )

    assert response.status_code == 422


def test_create_event_requires_event_date():
    response = client.post(
        "/events",
        headers=tenant_headers(),
        json={
            "name": "Plavi cvet",
            "event_time": "20:00:00",
        },
    )

    assert response.status_code == 422


def test_create_event_requires_event_time():
    response = client.post(
        "/events",
        headers=tenant_headers(),
        json={
            "name": "Plavi cvet",
            "event_date": "2026-11-05",
        },
    )

    assert response.status_code == 422


def test_create_event_requires_authentication():
    response = client.post(
        "/events",
        json={"name": "Plavi cvet"},
    )

    assert response.status_code == 401


def test_list_events():
    connection = MagicMock()
    connection.execute.return_value.fetchall.return_value = [
        (
            1,
            "Plavi cvet",
            date(2026, 11, 5),
            time(20, 0),
            None,
            "Plavi cvet",
            40,
            "Proslava",
            None,
            datetime(2026, 10, 21, 10, 0),
        )
    ]
    override_connection(connection)

    try:
        response = client.get("/events", headers=tenant_headers())

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Plavi cvet"
        connection.execute.assert_called_once()
    finally:
        app.dependency_overrides.clear()

def test_update_event_end_time():
    connection = MagicMock()
    connection.execute.side_effect = [
        MagicMock(
            fetchone=MagicMock(
                return_value=(
                    1,
                    "Plavi cvet",
                    date(2026, 11, 5),
                    time(20, 0),
                )
            )
        ),
        MagicMock(
            fetchone=MagicMock(
                return_value=(
                    1,
                    "Plavi cvet",
                    date(2026, 11, 5),
                    time(20, 0),
                    datetime(2026, 11, 6, 1, 0),
                    "Plavi cvet",
                    40,
                    "Proslava",
                    None,
                    datetime(2026, 10, 21, 10, 0),
                )
            )
        ),
    ]
    override_connection(connection)

    try:
        response = client.patch(
            "/events/1/end-time",
            headers=tenant_headers(),
            json={"ends_at": "2026-11-06T01:00:00"},
        )

        assert response.status_code == 200
        assert response.json()["ends_at"].startswith("2026-11-06T01:00:00")
        assert connection.execute.call_count == 2
    finally:
        app.dependency_overrides.clear()


def test_update_event_end_time_rejects_end_before_start():
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = (
        1,
        "Plavi cvet",
        date(2026, 11, 5),
        time(20, 0),
    )
    override_connection(connection)

    try:
        response = client.patch(
            "/events/1/end-time",
            headers=tenant_headers(),
            json={"ends_at": "2026-11-05T19:00:00"},
        )

        assert response.status_code == 422
        assert connection.execute.call_count == 1
    finally:
        app.dependency_overrides.clear()


def test_update_event_end_time_returns_not_found():
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = None
    override_connection(connection)

    try:
        response = client.patch(
            "/events/999/end-time",
            headers=tenant_headers(),
            json={"ends_at": "2026-11-06T01:00:00"},
        )

        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()

