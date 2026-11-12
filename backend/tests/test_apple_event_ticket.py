import copy
import json
from pathlib import Path

import pytest

from app.wallet.apple.event_ticket import map_canonical_ticket_to_apple


TEST_AUTHENTICATION_TOKEN = "test-authentication-token"


CANONICAL_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "app"
    / "wallet"
    / "canonical"
)


@pytest.fixture
def example():
    with (CANONICAL_DIR / "example.json").open(encoding="utf-8") as file:
        return json.load(file)


def test_maps_canonical_ticket_to_apple_event_ticket(example):
    result = map_canonical_ticket_to_apple(example, TEST_AUTHENTICATION_TOKEN)

    assert "eventTicket" in result
    assert "generic" not in result
    assert result["serialNumber"] == example["pass"]["serial_number"]
    assert result["organizationName"] == example["tenant"]["name"]
    assert result["authenticationToken"] == TEST_AUTHENTICATION_TOKEN


def test_maps_event_fields(example):
    result = map_canonical_ticket_to_apple(example, TEST_AUTHENTICATION_TOKEN)
    fields = result["eventTicket"]

    assert fields["primaryFields"][0]["value"] == example["event"]["name"]
    assert fields["secondaryFields"][0]["value"] == "15.11.2026. 20:00"
    assert fields["secondaryFields"][1]["value"] == example["event"]["location"]
    assert fields["auxiliaryFields"][0]["value"] == example["holder"]["name"]
    assert fields["headerFields"][0]["value"] == example["ticket_type"]["name"]


def test_maps_back_fields(example):
    result = map_canonical_ticket_to_apple(example, TEST_AUTHENTICATION_TOKEN)
    fields = result["eventTicket"]["backFields"]

    assert fields[0]["value"] == example["ticket_type"]["description"]
    assert fields[1]["value"] == example["tenant"]["name"]
    assert fields[2]["value"] == "15.11.2026. 23:00"


def test_maps_visual_properties(example):
    result = map_canonical_ticket_to_apple(example, TEST_AUTHENTICATION_TOKEN)

    assert result["logoText"] == example["visual"]["logo_text"]
    assert result["foregroundColor"] == "rgb(0, 0, 0)"
    assert result["backgroundColor"] == "rgb(255, 255, 255)"


def test_rejects_invalid_canonical_data(example):
    invalid = copy.deepcopy(example)
    del invalid["event"]["location"]

    with pytest.raises(ValueError, match="location"):
        map_canonical_ticket_to_apple(invalid, TEST_AUTHENTICATION_TOKEN)


def test_omits_location_field_when_event_location_is_empty(example):
    example["event"]["location"] = ""

    result = map_canonical_ticket_to_apple(
        example,
        TEST_AUTHENTICATION_TOKEN,
    )
    fields = result["eventTicket"]["secondaryFields"]

    assert len(fields) == 1
    assert fields[0]["key"] == "eventDate"

