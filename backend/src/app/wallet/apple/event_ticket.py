import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
from app.config.settings import settings

from app.wallet.canonical.validator import validate_ticket


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = BASE_DIR / "template" / "event_ticket.json"


def map_canonical_ticket_to_apple(
    canonical_data: dict[str, Any],
    authentication_token: str,
) -> dict[str, Any]:
    """Map canonical ticket data to an Apple eventTicket pass structure."""
    validate_ticket(canonical_data)

    with TEMPLATE_PATH.open(encoding="utf-8") as file:
        pass_data = json.load(file)

    data = deepcopy(pass_data)
    data["passTypeIdentifier"] = settings.apple_pass_type_identifier

    if settings.apple_web_service_url:
        data["webServiceURL"] = settings.apple_web_service_url

    data["authenticationToken"] = authentication_token

    tenant = canonical_data["tenant"]
    event = canonical_data["event"]
    holder = canonical_data["holder"]
    ticket_type = canonical_data["ticket_type"]
    visual = canonical_data["visual"]

    starts_at = datetime.fromisoformat(
        event["starts_at"].replace("Z", "+00:00")
    )
    ends_at = datetime.fromisoformat(
        event["ends_at"].replace("Z", "+00:00")
    )

    data["serialNumber"] = canonical_data["pass"]["serial_number"]
    data["organizationName"] = tenant["name"]
    data["logoText"] = visual["logo_text"]
    data["foregroundColor"] = _hex_to_rgb(visual["foreground_color"])
    data["backgroundColor"] = _hex_to_rgb(visual["background_color"])

    data["eventTicket"]["headerFields"] = [
        {
            "key": "ticketType",
            "label": "TIP KARTE",
            "value": ticket_type["name"],
        }
    ]

    data["eventTicket"]["primaryFields"] = [
        {
            "key": "eventName",
            "label": "DOGAĐAJ",
            "value": event["name"],
        }
    ]

    data["eventTicket"]["secondaryFields"] = [
        {
            "key": "eventDate",
            "label": "DATUM I VREME",
            "value": starts_at.strftime("%d.%m.%Y. %H:%M"),
        },
    ]

    if event["location"].strip():
        data["eventTicket"]["secondaryFields"].append(
            {
                "key": "eventLocation",
                "label": "LOKACIJA",
                "value": event["location"],
            }
        )

    data["eventTicket"]["auxiliaryFields"] = [
        {
            "key": "holderName",
            "label": "NOSILAC",
            "value": holder["name"],
        }
    ]

    data["eventTicket"]["backFields"] = [
        {
            "key": "ticketDescription",
            "label": "OPIS KARTE",
            "value": ticket_type.get("description", ""),
        },
        {
            "key": "organization",
            "label": "ORGANIZATOR",
            "value": tenant["name"],
        },
        {
            "key": "eventEnd",
            "label": "ZAVRŠETAK DOGAĐAJA",
            "value": ends_at.strftime("%d.%m.%Y. %H:%M"),
        },
    ]

    return data


def _hex_to_rgb(color: str) -> str:
    """Convert #RRGGBB to Apple's rgb(r, g, b) color format."""
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    return f"rgb({red}, {green}, {blue})"
