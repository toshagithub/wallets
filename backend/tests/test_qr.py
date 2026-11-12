
from app.wallet import qr


def test_valid_qr_signature():
    content = qr.generate_signed_qr_content(tenant_id=1, serial_number="TK-2026-000001-3")

    assert qr.verify_signed_qr_content(content) is True


def test_modified_serial_number_is_rejected():
    content = qr.generate_signed_qr_content(tenant_id=1, serial_number="TK-2026-000001-3")
    modified = content.replace("TK-2026-000001-3", "TK-2026-000002-4")

    assert qr.verify_signed_qr_content(modified) is False


def test_modified_tenant_id_is_rejected():
    content = qr.generate_signed_qr_content(tenant_id=1, serial_number="TK-2026-000001-3")
    modified = content.replace("|1|", "|2|", 1)

    assert qr.verify_signed_qr_content(modified) is False


def test_modified_signature_is_rejected():
    content = qr.generate_signed_qr_content(tenant_id=1, serial_number="TK-2026-000001-3")
    parts = content.split("|")
    parts[3] = ("0" if parts[3][0] != "0" else "1") + parts[3][1:]
    modified = "|".join(parts)

    assert qr.verify_signed_qr_content(modified) is False


def test_malformed_qr_content_is_rejected():
    assert qr.verify_signed_qr_content("neispravan-sadrzaj") is False
    assert qr.verify_signed_qr_content("v2|1|TK-2026-000001-3|invalid") is False
    assert qr.verify_signed_qr_content("v1|0|TK-2026-000001-3|" + "a" * 64) is False
