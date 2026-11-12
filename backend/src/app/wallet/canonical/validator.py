import json
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


BASE_DIR = Path(__file__).resolve().parent

with (BASE_DIR / "schema.json").open(encoding="utf-8") as file:
    SCHEMA = json.load(file)

Draft202012Validator.check_schema(SCHEMA)

_VALIDATOR = Draft202012Validator(
    SCHEMA,
    format_checker=FormatChecker(),
)


def validate_ticket(data: dict[str, Any]) -> None:
    """Validate canonical ticket data; raise ValueError if invalid."""
    errors = sorted(
        _VALIDATOR.iter_errors(data),
        key=lambda error: list(map(str, error.absolute_path)),
    )

    if errors:
        details = "; ".join(
            f"{'.'.join(map(str, error.absolute_path)) or '<root>'}: "
            f"{error.message}"
            for error in errors
        )
        raise ValueError(f"Invalid canonical ticket: {details}")

    starts_at = datetime.fromisoformat(
        data["event"]["starts_at"].replace("Z", "+00:00")
    )
    ends_at = datetime.fromisoformat(
        data["event"]["ends_at"].replace("Z", "+00:00")
    )

    if ends_at <= starts_at:
        raise ValueError(
            "Invalid canonical ticket: event.ends_at must be "
            "after event.starts_at"
        )
