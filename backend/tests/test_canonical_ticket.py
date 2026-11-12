import copy
import json
from pathlib import Path

import pytest

from app.wallet.canonical.validator import SCHEMA, validate_ticket
from jsonschema import Draft202012Validator


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


def test_schema_is_valid():
    Draft202012Validator.check_schema(SCHEMA)


def test_example_is_valid(example):
    validate_ticket(example)


def test_missing_required_event_field_is_rejected(example):
    invalid = copy.deepcopy(example)
    del invalid["event"]["location"]

    with pytest.raises(ValueError, match="location"):
        validate_ticket(invalid)



def test_empty_event_location_is_valid(example):
    data = copy.deepcopy(example)
    data["event"]["location"] = ""

    validate_ticket(data)

def test_invalid_email_is_rejected(example):
    invalid = copy.deepcopy(example)
    invalid["holder"]["email"] = "not-an-email"

    with pytest.raises(ValueError, match="email"):
        validate_ticket(invalid)


def test_invalid_color_is_rejected(example):
    invalid = copy.deepcopy(example)
    invalid["visual"]["background_color"] = "blue"

    with pytest.raises(ValueError, match="background_color"):
        validate_ticket(invalid)


def test_unknown_top_level_field_is_rejected(example):
    invalid = copy.deepcopy(example)
    invalid["unexpected"] = True

    with pytest.raises(ValueError, match="unexpected"):
        validate_ticket(invalid)


def test_rejects_event_ending_before_it_starts(example):
    data = copy.deepcopy(example)
    data["event"]["starts_at"] = "2026-11-15T23:00:00+01:00"
    data["event"]["ends_at"] = "2026-11-15T20:00:00+01:00"

    with pytest.raises(ValueError, match="event.ends_at must be after event.starts_at"):
        validate_ticket(data)

def test_rejects_string_pass_id(example):
    invalid = copy.deepcopy(example)
    invalid["pass"]["id"] = "PASS-TEST-001"

    with pytest.raises(ValueError, match="pass.id"):
        validate_ticket(invalid)
