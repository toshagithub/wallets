from datetime import datetime, timezone
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.db.dependencies import get_tenant_connection
from app.main import app
from app.wallet.qr import generate_signed_qr_content


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


def scan_payload(qr_content: str) -> dict:
    return {
        "qr_content": qr_content,
        "device_registration_id": 1,
    }


def setup_device_and_scan_log(connection: MagicMock) -> None:
    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),  # uređaj
        MagicMock(fetchone=MagicMock(return_value=(datetime.now(timezone.utc),))),
    ]


def test_scan_rejects_invalid_qr():
    connection = MagicMock()
    setup_device_and_scan_log(connection)
    override_connection(connection)

    try:
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload("neispravan-qr"),
        )

        assert response.status_code == 200
        assert response.json()["result"] == "NE POSTOJI"
    finally:
        app.dependency_overrides.clear()


def test_scan_rejects_missing_authentication():
    response = client.post(
        "/scanner/scan",
        json=scan_payload("neispravan-qr"),
    )

    assert response.status_code == 401


def test_scan_rejects_invalid_device():
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = None
    override_connection(connection)

    try:
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload("neispravan-qr"),
        )

        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_scan_returns_not_found_for_unknown_pass():
    connection = MagicMock()
    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),  # uređaj
        MagicMock(fetchone=MagicMock(return_value=None)),  # ulaznica
        MagicMock(fetchone=MagicMock(return_value=(datetime.now(timezone.utc),))),
    ]
    override_connection(connection)

    try:
        qr_content = generate_signed_qr_content(1001, "unknown-serial")
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload(qr_content),
        )

        assert response.status_code == 200
        assert response.json()["result"] == "NE POSTOJI"
    finally:
        app.dependency_overrides.clear()


def test_scan_returns_already_scanned():
    connection = MagicMock()
    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),  # uređaj
        MagicMock(
            fetchone=MagicMock(
                return_value=(
                    42,
                    "skeniran",
                    None,
                    None,
                )
            )
        ),  # ulaznica
        MagicMock(fetchone=MagicMock(return_value=(datetime.now(timezone.utc),))),
    ]
    override_connection(connection)

    try:
        qr_content = generate_signed_qr_content(1001, "serial-42")
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload(qr_content),
        )

        assert response.status_code == 200
        assert response.json()["result"] == "VEĆ OČITANA"
    finally:
        app.dependency_overrides.clear()


def test_scan_returns_cancelled_pass():
    connection = MagicMock()
    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),  # uređaj
        MagicMock(
            fetchone=MagicMock(
                return_value=(
                    42,
                    "poništen",
                    None,
                    None,
                )
            )
        ),  # ulaznica
        MagicMock(fetchone=MagicMock(return_value=(datetime.now(timezone.utc),))),
    ]
    override_connection(connection)

    try:
        qr_content = generate_signed_qr_content(1001, "serial-42")
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload(qr_content),
        )

        assert response.status_code == 200
        assert response.json()["result"] == "PONIŠTENA"
    finally:
        app.dependency_overrides.clear()
def test_scan_accepts_valid_pass():
    connection = MagicMock()
    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),  # registrovan uređaj
        MagicMock(
            fetchone=MagicMock(
                return_value=(
                    42,
                    "poslat",
                    None,
                    None,
                )
            )
        ),  # važeća ulaznica
        MagicMock(fetchone=MagicMock(return_value=(42,))),  # UPDATE prihvatio ulaznicu
        MagicMock(
            fetchone=MagicMock(
                return_value=(datetime.now(timezone.utc),)
            )
        ),  # evidencija skeniranja
    ]
    override_connection(connection)

    try:
        qr_content = generate_signed_qr_content(1001, "serial-42")
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload(qr_content),
        )

        assert response.status_code == 200
        assert response.json()["result"] == "VAŽI"
        assert response.json()["message"] == "Ulaznica je prihvaćena."
        assert connection.execute.call_count == 4
    finally:
        app.dependency_overrides.clear()
def test_scan_rejects_pass_before_valid_from():
    from datetime import timedelta

    connection = MagicMock()
    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),
        MagicMock(
            fetchone=MagicMock(
                return_value=(
                    42,
                    "poslat",
                    datetime.now(timezone.utc) + timedelta(hours=1),
                    None,
                )
            )
        ),
        MagicMock(
            fetchone=MagicMock(
                return_value=(datetime.now(timezone.utc),)
            )
        ),
    ]
    override_connection(connection)

    try:
        qr_content = generate_signed_qr_content(1001, "serial-42")
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload(qr_content),
        )

        assert response.status_code == 200
        assert response.json()["result"] == "ISTEKLA"
    finally:
        app.dependency_overrides.clear()


def test_scan_rejects_pass_after_valid_until():
    from datetime import timedelta

    connection = MagicMock()
    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),
        MagicMock(
            fetchone=MagicMock(
                return_value=(
                    42,
                    "poslat",
                    None,
                    datetime.now(timezone.utc) - timedelta(hours=1),
                )
            )
        ),
        MagicMock(
            fetchone=MagicMock(
                return_value=(datetime.now(timezone.utc),)
            )
        ),
    ]
    override_connection(connection)

    try:
        qr_content = generate_signed_qr_content(1001, "serial-42")
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload(qr_content),
        )

        assert response.status_code == 200
        assert response.json()["result"] == "ISTEKLA"
    finally:
        app.dependency_overrides.clear()


def test_scan_rejects_unexpected_pass_status():
    connection = MagicMock()
    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),  # registrovan uređaj
        MagicMock(
            fetchone=MagicMock(
                return_value=(
                    42,
                    "nepoznat_status",
                    None,
                    None,
                )
            )
        ),  # ulaznica sa neočekivanim statusom
    ]
    override_connection(connection)

    try:
        qr_content = generate_signed_qr_content(1001, "serial-42")
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload(qr_content),
        )

        assert response.status_code == 500
        assert connection.execute.call_count == 2
    finally:
        app.dependency_overrides.clear()

def test_scan_records_successful_scan():
    connection = MagicMock()
    scanned_at = datetime.now(timezone.utc)

    connection.execute.side_effect = [
        MagicMock(fetchone=MagicMock(return_value=(1,))),
        MagicMock(
            fetchone=MagicMock(
                return_value=(42, "poslat", None, None)
            )
        ),
        MagicMock(fetchone=MagicMock(return_value=(42,))),
        MagicMock(fetchone=MagicMock(return_value=(scanned_at,))),
    ]
    override_connection(connection)

    try:
        qr_content = generate_signed_qr_content(1001, "serial-42")
        response = client.post(
            "/scanner/scan",
            headers=tenant_headers(),
            json=scan_payload(qr_content),
        )

        assert response.status_code == 200
        assert response.json()["result"] == "VAŽI"

        insert_call = connection.execute.call_args_list[3]
        sql = insert_call.args[0]
        params = insert_call.args[1]

        assert "INSERT INTO skeniranje" in sql
        assert "tenant_id" in sql
        assert "pass_id" in sql
        assert "device_registration_id" in sql
        assert "user_id" in sql
        assert "result" in sql
        assert "method" in sql
        assert "scanned_at" in sql

        assert params == (1001, 42, 1, 1, "VAŽI")
        assert "'QR'" in sql
        assert "CURRENT_TIMESTAMP" in sql
    finally:
        app.dependency_overrides.clear()
