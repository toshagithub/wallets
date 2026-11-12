from typing import Any

from app.wallet.canonical.validator import validate_ticket
from app.wallet.qr import generate_signed_qr_content


def map_canonical_ticket_to_google(
    canonical_data: dict[str, Any],
    issuer_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Map canonical ticket data to Google EventTicketClass and EventTicketObject."""
    validate_ticket(canonical_data)

    if not issuer_id or not issuer_id.isdigit():
        raise ValueError("Google Wallet issuer ID mora biti numerički.")

    tenant = canonical_data["tenant"]
    event = canonical_data["event"]
    holder = canonical_data["holder"]
    ticket_type = canonical_data["ticket_type"]
    visual = canonical_data["visual"]
    serial_number = canonical_data["pass"]["serial_number"]
    tenant_id = tenant["id"]

    class_id = f"{issuer_id}.event_{tenant_id}_{event['id']}"
    object_id = f"{issuer_id}.ticket_{tenant_id}_{serial_number}"

    event_ticket_class = {
        "id": class_id,
        "issuerName": tenant["name"],
        "eventId": f"{tenant_id}_{event['id']}",
        "eventName": {
            "defaultValue": {
                "language": "sr",
                "value": event["name"],
            }
        },
        "dateTime": {
            "start": event["starts_at"],
            "end": event["ends_at"],
        },
        "hexBackgroundColor": visual["background_color"],
        "reviewStatus": "UNDER_REVIEW",
    }

    if event["location"].strip():
        event_ticket_class["venue"] = {
            "name": {
                "defaultValue": {
                    "language": "sr",
                    "value": event["location"],
                }
            },
            "address": {
                "defaultValue": {
                    "language": "sr",
                    "value": event["location"],
                }
            },
        }

    event_ticket_object = {
        "id": object_id,
        "classId": class_id,
        "state": "ACTIVE",
        "ticketHolderName": holder["name"],
        "ticketNumber": serial_number,
        "ticketType": {
            "defaultValue": {
                "language": "sr",
                "value": ticket_type["name"],
            }
        },
        "barcode": {
            "type": "QR_CODE",
            "value": generate_signed_qr_content(
                tenant_id=tenant_id,
                serial_number=serial_number,
            ),
            "alternateText": serial_number,
        },
        "hexBackgroundColor": visual["background_color"],
        "textModulesData": [
            {
                "id": "ticket_description",
                "header": "Opis karte",
                "body": ticket_type.get("description", ""),
            }
        ],
    }

    return event_ticket_class, event_ticket_object
