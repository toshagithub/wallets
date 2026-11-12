import json
from pathlib import Path
from types import SimpleNamespace

from app.wallet.google import generator
from app.wallet.qr import verify_signed_qr_content


EXAMPLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "app"
    / "wallet"
    / "canonical"
    / "example.json"
)


def test_google_event_ticket_pass_uses_class_object_and_signed_qr(monkeypatch):
    canonical_data = json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    )
    inserted_classes = []
    inserted_objects = []

    class FakeRequest:
        def __init__(self, response):
            self.response = response

        def execute(self):
            return self.response

    class FakeEventTicketClass:
        def get(self, resourceId):
            return FakeRequest({"id": resourceId, "reviewStatus": "approved"})

        def insert(self, body):
            inserted_classes.append(body)
            return FakeRequest({"id": body["id"], "reviewStatus": "approved"})

    class FakeEventTicketObject:
        def insert(self, body):
            inserted_objects.append(body)
            return FakeRequest({"id": body["id"], "reviewStatus": "approved"})

    fake_service = SimpleNamespace(
        eventticketclass=lambda: FakeEventTicketClass(),
        eventticketobject=lambda: FakeEventTicketObject(),
    )
    fake_credentials = SimpleNamespace(
        service_account_email="test@example.com",
        signer=object(),
    )
    encoded_payloads = []

    monkeypatch.setattr(
        generator.service_account.Credentials,
        "from_service_account_file",
        lambda *args, **kwargs: fake_credentials,
    )
    monkeypatch.setattr(
        generator,
        "build",
        lambda *args, **kwargs: fake_service,
    )
    monkeypatch.setattr(
        generator.jwt,
        "encode",
        lambda signer, payload: (
            encoded_payloads.append(payload) or b"fake-event-jwt"
        ),
    )

    save_url = generator.generate_google_event_ticket_pass(canonical_data)

    assert inserted_classes == []
    assert len(inserted_objects) == 1

    ticket_object = inserted_objects[0]
    expected_class_id = f"{generator.settings.google_wallet_issuer_id}.event_1_1"
    assert ticket_object["classId"] == expected_class_id
    assert ticket_object["ticketNumber"] == "TKT-TEST-001"

    qr_content = ticket_object["barcode"]["value"]
    assert qr_content.startswith("v1|1|TKT-TEST-001|")
    assert verify_signed_qr_content(qr_content)

    assert encoded_payloads[0]["payload"]["eventTicketObjects"] == [
        {
            "id": ticket_object["id"],
            "classId": ticket_object["classId"],
        }
    ]
    assert save_url == (
        "https://pay.google.com/gp/v/save/fake-event-jwt"
    )


def test_google_event_ticket_pass_creates_class_when_missing(monkeypatch):
    canonical_data = json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    )
    inserted_classes = []
    inserted_objects = []

    class FakeResponse:
        status = 404

    class FakeHttpError(Exception):
        resp = FakeResponse()

    class FakeRequest:
        def __init__(self, response=None, error=None):
            self.response = response
            self.error = error

        def execute(self):
            if self.error:
                raise self.error
            return self.response

    class FakeEventTicketClass:
        def get(self, resourceId):
            return FakeRequest(error=FakeHttpError("Class not found"))

        def insert(self, body):
            inserted_classes.append(body)
            return FakeRequest({"id": body["id"], "reviewStatus": "approved"})

    class FakeEventTicketObject:
        def insert(self, body):
            inserted_objects.append(body)
            return FakeRequest({"id": body["id"], "reviewStatus": "approved"})

    fake_service = SimpleNamespace(
        eventticketclass=lambda: FakeEventTicketClass(),
        eventticketobject=lambda: FakeEventTicketObject(),
    )
    fake_credentials = SimpleNamespace(
        service_account_email="test@example.com",
        signer=object(),
    )

    monkeypatch.setattr(
        generator.service_account.Credentials,
        "from_service_account_file",
        lambda *args, **kwargs: fake_credentials,
    )
    monkeypatch.setattr(
        generator,
        "build",
        lambda *args, **kwargs: fake_service,
    )
    monkeypatch.setattr(
        generator.jwt,
        "encode",
        lambda signer, payload: b"fake-event-jwt",
    )

    save_url = generator.generate_google_event_ticket_pass(canonical_data)

    expected_class_id = (
        f"{generator.settings.google_wallet_issuer_id}.event_1_1"
    )
    assert len(inserted_classes) == 1
    assert inserted_classes[0]["id"] == expected_class_id
    assert len(inserted_objects) == 1
    assert inserted_objects[0]["classId"] == expected_class_id
    assert save_url == "https://pay.google.com/gp/v/save/fake-event-jwt"


def test_google_event_ticket_pass_propagates_existing_object_error(monkeypatch):
    canonical_data = json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    )

    class FakeRequest:
        def execute(self):
            return {"id": "existing-class", "reviewStatus": "approved"}

    class FakeEventTicketClass:
        def get(self, resourceId):
            return FakeRequest()

    class FakeEventTicketObject:
        def insert(self, body):
            raise RuntimeError("Object already exists")

    fake_service = SimpleNamespace(
        eventticketclass=lambda: FakeEventTicketClass(),
        eventticketobject=lambda: FakeEventTicketObject(),
    )
    fake_credentials = SimpleNamespace(
        service_account_email="test@example.com",
        signer=object(),
    )

    monkeypatch.setattr(
        generator.service_account.Credentials,
        "from_service_account_file",
        lambda *args, **kwargs: fake_credentials,
    )
    monkeypatch.setattr(
        generator,
        "build",
        lambda *args, **kwargs: fake_service,
    )

    import pytest

    with pytest.raises(RuntimeError, match="Object already exists"):
        generator.generate_google_event_ticket_pass(canonical_data)


def test_google_event_ticket_pass_rejects_class_not_ready(monkeypatch):
    import pytest

    canonical_data = json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    )
    inserted_objects = []

    class FakeRequest:
        def execute(self):
            return {"id": "class-id", "reviewStatus": "underReview"}

    class FakeEventTicketClass:
        def get(self, resourceId):
            return FakeRequest()

    class FakeEventTicketObject:
        def insert(self, body):
            inserted_objects.append(body)
            return FakeRequest()

    fake_service = SimpleNamespace(
        eventticketclass=lambda: FakeEventTicketClass(),
        eventticketobject=lambda: FakeEventTicketObject(),
    )
    fake_credentials = SimpleNamespace(
        service_account_email="test@example.com",
        signer=object(),
    )

    monkeypatch.setattr(
        generator.service_account.Credentials,
        "from_service_account_file",
        lambda *args, **kwargs: fake_credentials,
    )
    monkeypatch.setattr(
        generator,
        "build",
        lambda *args, **kwargs: fake_service,
    )

    monkeypatch.setattr(
        generator.jwt,
        "encode",
        lambda signer, payload: b"fake-event-jwt",
    )

    with pytest.raises(ValueError, match="class"):
        generator.generate_google_event_ticket_pass(canonical_data)

    assert inserted_objects == []


def test_google_event_ticket_pass_reuses_existing_object(monkeypatch):
    import json
    from pathlib import Path
    from types import SimpleNamespace

    canonical_data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))
    inserted_objects = []
    fetched_objects = []

    class FakeResponse:
        status = 409

    class FakeHttpError(Exception):
        resp = FakeResponse()

    class FakeRequest:
        def __init__(self, response=None, error=None):
            self.response = response
            self.error = error

        def execute(self):
            if self.error:
                raise self.error
            return self.response

    class FakeEventTicketClass:
        def get(self, resourceId):
            return FakeRequest({
                "id": resourceId,
                "reviewStatus": "approved",
            })

    class FakeEventTicketObject:
        def insert(self, body):
            inserted_objects.append(body)
            raise FakeHttpError("Object already exists")

        def get(self, resourceId):
            fetched_objects.append(resourceId)
            return FakeRequest({"id": resourceId, "state": "ACTIVE"})

    fake_service = SimpleNamespace(
        eventticketclass=lambda: FakeEventTicketClass(),
        eventticketobject=lambda: FakeEventTicketObject(),
    )
    fake_credentials = SimpleNamespace(
        service_account_email="test@example.com",
        signer=object(),
    )

    monkeypatch.setattr(
        generator.service_account.Credentials,
        "from_service_account_file",
        lambda *args, **kwargs: fake_credentials,
    )
    monkeypatch.setattr(generator, "build", lambda *args, **kwargs: fake_service)
    monkeypatch.setattr(
        generator.jwt,
        "encode",
        lambda signer, payload: b"fake-event-jwt",
    )

    save_url = generator.generate_google_event_ticket_pass(canonical_data)

    expected_object_id = (
        f"{generator.settings.google_wallet_issuer_id}.ticket_1_TKT-TEST-001"
    )
    assert len(inserted_objects) == 1
    assert fetched_objects == [expected_object_id]
    assert save_url == "https://pay.google.com/gp/v/save/fake-event-jwt"


def test_google_event_ticket_pass_propagates_class_api_error(monkeypatch):
    import pytest

    canonical_data = json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    )
    inserted_objects = []

    class FakeResponse:
        status = 403

    class FakeHttpError(Exception):
        resp = FakeResponse()

    class FakeRequest:
        def execute(self):
            raise FakeHttpError("Permission denied")

    class FakeEventTicketClass:
        def get(self, resourceId):
            return FakeRequest()

    class FakeEventTicketObject:
        def insert(self, body):
            inserted_objects.append(body)

    fake_service = SimpleNamespace(
        eventticketclass=lambda: FakeEventTicketClass(),
        eventticketobject=lambda: FakeEventTicketObject(),
    )
    fake_credentials = SimpleNamespace(
        service_account_email="test@example.com",
        signer=object(),
    )

    monkeypatch.setattr(
        generator.service_account.Credentials,
        "from_service_account_file",
        lambda *args, **kwargs: fake_credentials,
    )
    monkeypatch.setattr(
        generator,
        "build",
        lambda *args, **kwargs: fake_service,
    )

    with pytest.raises(FakeHttpError, match="Permission denied"):
        generator.generate_google_event_ticket_pass(canonical_data)

    assert inserted_objects == []
