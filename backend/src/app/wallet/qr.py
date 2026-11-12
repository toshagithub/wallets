
import hashlib
import hmac

from app.config.settings import settings


def generate_signed_qr_content(tenant_id: int, serial_number: str) -> str:
    """Generate versioned QR content signed with HMAC-SHA-256."""
    payload = f"v1|{tenant_id}|{serial_number}"
    signature = hmac.new(
        settings.hmac_secret.encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()

    return f"{payload}|{signature}"


def verify_signed_qr_content(content: str) -> bool:
    """Verify signed QR content; return False for malformed or altered data."""
    try:
        parts = content.split("|")
        if len(parts) != 4:
            return False

        version, tenant_id, serial_number, signature = parts

        if version != "v1":
            return False
        if not tenant_id.isdigit() or int(tenant_id) <= 0:
            return False
        if not serial_number or len(signature) != 64:
            return False
        if any(char not in "0123456789abcdef" for char in signature):
            return False

        payload = f"{version}|{tenant_id}|{serial_number}"
        expected_signature = hmac.new(
            settings.hmac_secret.encode("utf-8"),
            payload.encode("ascii"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
    except (ValueError, UnicodeEncodeError):
        return False
