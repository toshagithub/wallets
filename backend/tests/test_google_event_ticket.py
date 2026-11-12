import json
from pathlib import Path

from app.wallet.google.event_ticket import map_canonical_ticket_to_google
from app.wallet.qr import verify_signed_qr_content


EXAMPLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "app"
    / "wallet"
    / "canonical"
    / "example.json"
)


def test_maps_canonical_ticket_to_google_event_ticket():
    canonical_data = json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    )

    event_class, ticket_object = map_canonical_ticket_to_google(
        canonical_data,
        issuer_id="123456789",
    )

    assert event_class["id"] == "123456789.event_1_1"
    assert (
        event_class["eventName"]["defaultValue"]["value"]
        == "Demo koncert"
    )
    assert (
        event_class["venue"]["name"]["defaultValue"]["value"]
        == "Beograd, Štark arena"
    )
    assert event_class["dateTime"]["start"] == "2026-11-15T20:00:00+01:00"
    assert event_class["dateTime"]["end"] == "2026-11-15T23:00:00+01:00"

    assert ticket_object["id"] == "123456789.ticket_1_TKT-TEST-001"
    assert ticket_object["classId"] == event_class["id"]
    assert ticket_object["ticketHolderName"] == "Petar Petrović"
    assert ticket_object["ticketNumber"] == "TKT-TEST-001"
    assert (
        ticket_object["ticketType"]["defaultValue"]["value"]
        == "Standard"
    )

    qr_content = ticket_object["barcode"]["value"]
    assert qr_content.startswith("v1|1|TKT-TEST-001|")
    assert verify_signed_qr_content(qr_content)


def test_rejects_non_numeric_issuer_id():
    canonical_data = json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    )

    try:
        map_canonical_ticket_to_google(canonical_data, issuer_id="demo")
    except ValueError as error:
        assert "issuer ID" in str(error)
    else:
        raise AssertionError("Očekivano je odbacivanje neispravnog issuer ID-ja.")


def test_omits_venue_when_event_location_is_empty():
    canonical_data = json.loads(
        EXAMPLE_PATH.read_text(encoding="utf-8")
    )
    canonical_data["event"]["location"] = ""

    event_class, _ = map_canonical_ticket_to_google(
        canonical_data,
        issuer_id="123456789",
    )

    assert "venue" not in event_class

