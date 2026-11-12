import time

from google.auth import jwt
from google.oauth2 import service_account
from googleapiclient.discovery import build

from app.config.settings import settings
from app.wallet.qr import generate_signed_qr_content


SCOPES = ["https://www.googleapis.com/auth/wallet_object.issuer"]
CLASS_SUFFIX = "wallets_test_generic"


def generate_google_wallet_pass(
    tenant_id: int,
    serial_number: str,
) -> str:
    """Kreira Google Wallet test pass sa serijskim brojem i potpisanim QR-om."""

    credentials = service_account.Credentials.from_service_account_file(
        settings.google_service_account_path,
        scopes=SCOPES,
    )

    wallet_service = build(
        "walletobjects",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    issuer_id = settings.google_wallet_issuer_id
    class_id = f"{issuer_id}.{CLASS_SUFFIX}"
    object_id = f"{issuer_id}.wallets_{tenant_id}_{serial_number}"

    try:
        wallet_service.genericclass().get(
            resourceId=class_id,
        ).execute()
    except Exception as error:
        if getattr(getattr(error, "resp", None), "status", None) != 404:
            raise

        wallet_service.genericclass().insert(
            body={
                "id": class_id,
                "issuerName": "Wallets Test",
            }
        ).execute()

    qr_content = generate_signed_qr_content(
        tenant_id=tenant_id,
        serial_number=serial_number,
    )

    generic_object = {
        "id": object_id,
        "classId": class_id,
        "state": "ACTIVE",
        "barcode": {
            "type": "QR_CODE",
            "value": qr_content,
            "alternateText": serial_number,
        },
        "cardTitle": {
            "defaultValue": {
                "language": "sr",
                "value": "Wallets test",
            }
        },
        "header": {
            "defaultValue": {
                "language": "sr",
                "value": serial_number,
            }
        },
        "textModulesData": [
            {
                "header": "Serijski broj",
                "body": serial_number,
                "id": "serial_number",
            }
        ],
    }

    response = wallet_service.genericobject().insert(
        body=generic_object,
    ).execute()

    payload = {
        "iss": credentials.service_account_email,
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "origins": ["https://www.gstatic.com"],
        "payload": {
            "genericObjects": [{"id": response["id"]}],
        },
    }

    signed_jwt = jwt.encode(credentials.signer, payload).decode("utf-8")
    return f"https://pay.google.com/gp/v/save/{signed_jwt}"


def generate_google_event_ticket_pass(canonical_data: dict) -> str:
    """Kreira Google Wallet EventTicket pass i vraća Save to Google Wallet link."""
    from app.wallet.google.event_ticket import map_canonical_ticket_to_google

    credentials = service_account.Credentials.from_service_account_file(
        settings.google_service_account_path,
        scopes=SCOPES,
    )

    wallet_service = build(
        "walletobjects",
        "v1",
        credentials=credentials,
        cache_discovery=False,
    )

    event_ticket_class, event_ticket_object = map_canonical_ticket_to_google(
        canonical_data,
        issuer_id=settings.google_wallet_issuer_id,
    )

    class_id = event_ticket_class["id"]
    object_id = event_ticket_object["id"]

    try:
        class_response = wallet_service.eventticketclass().get(
            resourceId=class_id,
        ).execute()
    except Exception as error:
        if getattr(getattr(error, "resp", None), "status", None) != 404:
            raise

        class_response = wallet_service.eventticketclass().insert(
            body=event_ticket_class,
        ).execute()

    review_status = class_response.get("reviewStatus", "").lower()
    if review_status != "approved":
        raise ValueError(
            f"Google Wallet class {class_id} is not approved "
            f"(reviewStatus={review_status or 'missing'}); pass was not issued."
        )

    try:
        wallet_service.eventticketobject().insert(
            body=event_ticket_object,
        ).execute()
    except Exception as error:
        if getattr(getattr(error, "resp", None), "status", None) != 409:
            raise

        wallet_service.eventticketobject().get(
            resourceId=object_id,
        ).execute()

    payload = {
        "iss": credentials.service_account_email,
        "aud": "google",
        "typ": "savetowallet",
        "iat": int(time.time()),
        "origins": ["https://www.gstatic.com"],
        "payload": {
            "eventTicketObjects": [
                {
                    "id": object_id,
                    "classId": class_id,
                }
            ],
        },
    }

    signed_jwt = jwt.encode(credentials.signer, payload).decode("utf-8")
    return f"https://pay.google.com/gp/v/save/{signed_jwt}"
