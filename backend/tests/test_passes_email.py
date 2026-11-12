import asyncio
from datetime import date, datetime, time, timezone
from io import BytesIO
from unittest.mock import MagicMock
from zipfile import ZipFile

import pytest
from fastapi import HTTPException

from app.passes import router as passes_router


class FakeCursor:
    def __init__(self, *, one=None, all=None):
        self.one = one
        self.all = all

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.all


class FakeConnection:
    def __init__(
        self,
        guest_email,
        *,
        capacity=None,
        issued_count=0,
        existing_statuses=None,
    ):
        self.guest_email = guest_email
        self.capacity = capacity
        self.issued_count = issued_count
        self.existing_statuses = existing_statuses
        self.existing_passes = []
        self.available_guest_ids = [10]
        self.calls = []
        self.committed = False
        self.pass_inserted = False
        self.inserted_passes = []
        self.next_pass_id = 100
        self.platform_insertions = []

    def execute(self, query, params=None):
        self.calls.append(query)

        if "INSERT INTO pass_platform_issuance" in query:
            self.platform_insertions.append(params)
            return FakeCursor()

        if "SELECT id, capacity, ends_at" in query:
            return FakeCursor(
                one=(
                    1,
                    self.capacity,
                    datetime(2026, 12, 15, 22, 0, tzinfo=timezone.utc),
                )
            )

        if "SELECT COUNT(*)" in query:
            if "JOIN tip_karte t" in query:
                if self.existing_statuses is not None:
                    active_count = sum(
                        item_status != "poništen"
                        for item_status in self.existing_statuses
                    )
                    return FakeCursor(one=(active_count,))

                return FakeCursor(one=(self.issued_count,))

            return FakeCursor(one=(self.issued_count,))

        if "SELECT id, quantity_limit" in query:
            return FakeCursor(one=(1, None))

        if "SELECT id FROM primalac" in query:
            return FakeCursor(
                all=[(guest_id,) for guest_id in self.available_guest_ids]
            )

        if "SELECT recipient_id, id, serial_number" in query:
            return FakeCursor(all=self.existing_passes)

        if "INSERT INTO pass (" in query:
            self.pass_inserted = True
            self.inserted_passes.append(params)
            pass_id = self.next_pass_id
            self.next_pass_id += 1
            return FakeCursor(one=(pass_id,))

        if "SELECT id FROM pass_platform_issuance" in query:
            return FakeCursor(one=None)

        if "apple_authentication_token" in query:
            return FakeCursor(one=(None,))

        if "SELECT p.name, p.event_date" in query:
            return FakeCursor(
                one=(
                    "Konferencija 2026",
                    date(2026, 12, 15),
                    time(18, 30),
                    datetime(2026, 12, 15, 22, 0, tzinfo=timezone.utc),
                    "Beograd",
                    "Standard",
                    1500,
                    "RSD",
                    1,
                    "Wallets",
                    1,
                )
            )

        if "SELECT id, name, email, phone" in query and "FROM primalac" in query:
            guest_id = params[0]
            if guest_id not in self.available_guest_ids:
                return FakeCursor(one=None)

            return FakeCursor(
                one=(guest_id, f"Test gost {guest_id}", self.guest_email, None)
            )

        return FakeCursor()

    def commit(self):
        self.committed = True


@pytest.fixture
def setup_issue(monkeypatch):
    connection = FakeConnection("gost@example.com")
    events = []

    monkeypatch.setattr(
        passes_router,
        "generate_serial_number",
        lambda *args: "TEST-SERIAL-001",
    )
    monkeypatch.setattr(
        passes_router,
        "generate_google_event_ticket_pass",
        lambda canonical_data: "https://pay.google.com/gp/v/save/test-token",
    )

    original_commit = connection.commit

    def commit():
        original_commit()
        events.append("commit")

    connection.commit = commit

    monkeypatch.setattr(
        passes_router,
        "send_pass_email",
        lambda **kwargs: events.append("email"),
    )

    monkeypatch.setattr(
        passes_router,
        "build_google_pass_email",
        lambda *args: {
            "subject": "Vaša digitalna ulaznica",
            "text_body": "Test",
            "html_body": "<p>Test</p>",
        },
    )

    request = passes_router.IssuePassRequest(
        program_id=1,
        ticket_type_id=1,
        guest_ids=[10],
        platform="google",
    )

    return connection, events, request


def test_issue_pass_sends_email_after_commit(setup_issue):
    connection, events, request = setup_issue

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response["count"] == 1
    assert response["email_results"] == {
        "sent": 1,
        "failed": 0,
        "skipped": 0,
    }
    assert connection.pass_inserted is True
    assert events == ["commit", "email"]


def test_issue_pass_skips_email_without_guest_address(setup_issue):
    connection, events, request = setup_issue
    connection.guest_email = None

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response["count"] == 1
    assert response["email_results"] == {
        "sent": 0,
        "failed": 0,
        "skipped": 1,
    }
    assert connection.pass_inserted is True
    assert events == ["commit"]


def test_issue_pass_keeps_pass_when_email_fails(setup_issue, monkeypatch):
    connection, events, request = setup_issue

    def fail_sending(**kwargs):
        events.append("email")
        raise RuntimeError("SMTP test failure")

    monkeypatch.setattr(passes_router, "send_pass_email", fail_sending)

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response["count"] == 1
    assert response["email_results"] == {
        "sent": 0,
        "failed": 1,
        "skipped": 0,
    }
    assert connection.pass_inserted is True
    assert events == ["commit", "email"]


async def read_streaming_response(response):
    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    return b"".join(chunks)


def test_issue_apple_pass_emails_attachment_and_returns_zip(setup_issue, monkeypatch):
    connection, events, _ = setup_issue

    request = passes_router.IssuePassRequest(
        program_id=1,
        ticket_type_id=1,
        guest_ids=[10],
        platform="apple",
    )

    generated_pkpass = b"fake-apple-pass-content"
    email_calls = []

    monkeypatch.setattr(
        passes_router,
        "generate_apple_event_ticket",
        lambda canonical_data, authentication_token: generated_pkpass,
    )
    monkeypatch.setattr(
        passes_router,
        "build_apple_pass_email",
        lambda canonical_data: {
            "subject": "Vaša digitalna ulaznica",
            "text_body": "Test Apple",
            "html_body": "<p>Test Apple</p>",
        },
    )

    def capture_email(**kwargs):
        events.append("email")
        email_calls.append(kwargs)

    monkeypatch.setattr(passes_router, "send_pass_email", capture_email)

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response.media_type == "application/zip"
    assert response.headers["Content-Disposition"] == (
        'attachment; filename="apple_passes.zip"'
    )
    assert response.headers["X-Email-Results"] == (
        '{"sent": 1, "failed": 0, "skipped": 0}'
    )
    assert connection.pass_inserted is True
    assert events == ["commit", "email"]

    assert len(email_calls) == 1
    assert email_calls[0]["recipient"] == "gost@example.com"
    assert email_calls[0]["attachment_bytes"] == generated_pkpass
    assert email_calls[0]["attachment_filename"] == "TEST-SERIAL-001.pkpass"

    zip_bytes = asyncio.run(read_streaming_response(response))

    with ZipFile(BytesIO(zip_bytes)) as archive:
        assert archive.namelist() == ["TEST-SERIAL-001.pkpass"]
        assert archive.read("TEST-SERIAL-001.pkpass") == generated_pkpass


def test_issue_both_passes_sends_one_email_with_both_options(
    setup_issue, monkeypatch
):
    connection, events, _ = setup_issue

    request = passes_router.IssuePassRequest(
        program_id=1,
        ticket_type_id=1,
        guest_ids=[10],
        platform="both",
    )

    generated_pkpass = b"fake-apple-pass-content"
    generated_save_url = "https://pay.google.com/gp/v/save/test-token"
    email_calls = []

    monkeypatch.setattr(
        passes_router,
        "generate_apple_event_ticket",
        lambda canonical_data, authentication_token: generated_pkpass,
    )

    monkeypatch.setattr(
        passes_router,
        "build_both_pass_email",
        lambda canonical_data, save_url: {
            "subject": "Konferencija 2026 – Vaša digitalna ulaznica",
            "text_body": f"Apple prilog i Google link: {save_url}",
            "html_body": f"<p>Google Wallet: {save_url}</p>",
        },
    )

    def capture_email(**kwargs):
        events.append("email")
        email_calls.append(kwargs)

    monkeypatch.setattr(passes_router, "send_pass_email", capture_email)

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response["count"] == 1
    assert response["email_results"] == {
        "sent": 1,
        "failed": 0,
        "skipped": 0,
    }

    assert response["issued"][0]["save_url"] == generated_save_url

    assert connection.platform_insertions == [
        (1, 100, "apple"),
        (1, 100, "google"),
    ]

    assert events == ["commit", "email"]

    assert len(email_calls) == 1
    assert email_calls[0]["recipient"] == "gost@example.com"
    assert email_calls[0]["attachment_bytes"] == generated_pkpass
    assert email_calls[0]["attachment_filename"] == "TEST-SERIAL-001.pkpass"
    assert generated_save_url in email_calls[0]["text_body"]



@pytest.mark.parametrize(
    ("capacity", "issued_count"),
    [
        (10, 8),  # Ispod kapaciteta
        (10, 9),  # Tačno do kapaciteta
    ],
)
def test_issue_pass_respects_event_capacity(
    setup_issue, capacity, issued_count
):
    connection, _, request = setup_issue
    connection.capacity = capacity
    connection.issued_count = issued_count

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response["count"] == 1
    assert connection.pass_inserted is True
    assert connection.committed is True



@pytest.mark.parametrize(
    ("existing_status", "should_reject"),
    [
        ("poslat", True),
        ("otvoren", True),
        ("instaliran", True),
        ("uklonjen", True),
        ("skeniran", True),
        ("poništen", False),
    ],
)
def test_issue_pass_counts_capacity_by_status(
    setup_issue, existing_status, should_reject
):
    connection, _, request = setup_issue
    connection.capacity = 1
    connection.existing_statuses = [existing_status]

    if should_reject:
        with pytest.raises(HTTPException) as exc_info:
            passes_router.issue_passes(
                request,
                current_user={"tenant_id": 1},
                connection=connection,
            )

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail == "Dostignut je kapacitet događaja."
        assert connection.pass_inserted is False
        assert connection.committed is False
    else:
        response = passes_router.issue_passes(
            request,
            current_user={"tenant_id": 1},
            connection=connection,
        )

        assert response["count"] == 1
        assert connection.pass_inserted is True
        assert connection.committed is True


def test_issue_pass_rejects_exceeding_event_capacity(setup_issue):
    connection, _, request = setup_issue
    connection.capacity = 10
    connection.issued_count = 10

    with pytest.raises(HTTPException) as exc_info:
        passes_router.issue_passes(
            request,
            current_user={"tenant_id": 1},
            connection=connection,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Dostignut je kapacitet događaja."
    assert connection.pass_inserted is False
    assert connection.committed is False


def test_issue_group_passes_within_event_capacity(setup_issue):
    connection, events, request = setup_issue
    connection.capacity = 4
    connection.issued_count = 2
    connection.available_guest_ids = [10, 11]
    request.guest_ids = [10, 11]

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response["count"] == 2
    assert len(connection.inserted_passes) == 2
    assert connection.committed is True
    assert events.count("email") == 2


def test_issue_group_passes_rejected_when_exceeding_event_capacity(
    setup_issue,
):
    connection, events, request = setup_issue
    connection.capacity = 3
    connection.issued_count = 2
    connection.available_guest_ids = [10, 11]
    request.guest_ids = [10, 11]

    with pytest.raises(HTTPException) as exc_info:
        passes_router.issue_passes(
            request,
            current_user={"tenant_id": 1},
            connection=connection,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "Dostignut je kapacitet događaja."
    assert connection.inserted_passes == []
    assert connection.committed is False
    assert events == []


def test_reissue_existing_pass_on_another_platform(setup_issue):
    connection, events, request = setup_issue
    connection.capacity = 1
    connection.issued_count = 1
    connection.existing_passes = [(10, 77, "EXISTING-SERIAL-001")]

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response["count"] == 1
    assert response["issued"][0]["pass_id"] == 77
    assert response["issued"][0]["serial_number"] == "EXISTING-SERIAL-001"
    assert connection.inserted_passes == []
    assert connection.platform_insertions == [(1, 77, "google")]
    assert connection.committed is True
    assert events == ["commit", "email"]
    assert not any(
        "JOIN tip_karte t" in query and "SELECT COUNT(*)" in query
        for query in connection.calls
    )


def test_reissue_group_passes_on_another_platform(setup_issue):
    connection, events, request = setup_issue
    connection.capacity = 2
    connection.available_guest_ids = [10, 11]
    connection.existing_passes = [
        (10, 77, "EXISTING-SERIAL-001"),
        (11, 78, "EXISTING-SERIAL-002"),
    ]
    request.guest_ids = [10, 11]

    response = passes_router.issue_passes(
        request,
        current_user={"tenant_id": 1},
        connection=connection,
    )

    assert response["count"] == 2
    assert response["issued"] == [
        {
            "guest_id": 10,
            "pass_id": 77,
            "serial_number": "EXISTING-SERIAL-001",
            "save_url": "https://pay.google.com/gp/v/save/test-token",
        },
        {
            "guest_id": 11,
            "pass_id": 78,
            "serial_number": "EXISTING-SERIAL-002",
            "save_url": "https://pay.google.com/gp/v/save/test-token",
        },
    ]
    assert connection.inserted_passes == []
    assert connection.platform_insertions == [
        (1, 77, "google"),
        (1, 78, "google"),
    ]
    assert connection.committed is True
    assert events == ["commit", "email", "email"]

