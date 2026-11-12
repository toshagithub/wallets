import json
import zipfile
from io import BytesIO
from pathlib import Path

from app.wallet.apple import generator
from app.wallet.qr import verify_signed_qr_content


def test_generated_pass_contains_provided_serial_number(monkeypatch, tmp_path):
    expected_serial = "TA-2026-000123-4"
    tenant_id = 1

    template_dir = tmp_path / "template"
    template_dir.mkdir()

    (template_dir / "pass.json").write_text(
        json.dumps({
            "serialNumber": "",
            "authenticationToken": "",
            "barcodes": [
                {
                    "format": "PKBarcodeFormatQR",
                    "message": "KP001",
                }
            ],
            "generic": {
                "primaryFields": [{"value": ""}],
                "secondaryFields": [
                    {"value": ""},
                    {"value": ""},
                ],
            },
        }),
        encoding="utf-8",
    )
    (template_dir / "icon.png").write_bytes(b"test-icon")

    monkeypatch.setattr(generator, "TEMPLATE_DIR", template_dir)
    monkeypatch.setattr(
        generator,
        "load_apple_private_key",
        lambda: b"test-key",
    )

    def fake_subprocess_run(args, **kwargs):
        if "zip" in args:
            output_path = Path(args[3])
            with zipfile.ZipFile(output_path, "w") as archive:
                for file_path in (
                    template_dir / "icon.png",
                    Path(args[-1]).parent / "manifest.json",
                    Path(args[-1]).parent / "pass.json",
                    Path(args[-1]).parent / "signature",
                ):
                    if file_path.name == "signature":
                        file_path.write_bytes(b"test-signature")
                    archive.write(file_path, file_path.name)

        elif "smime" in args:
            output_index = args.index("-out") + 1
            Path(args[output_index]).write_bytes(b"test-signature")

    monkeypatch.setattr(generator.subprocess, "run", fake_subprocess_run)

    result = generator.generate_apple_pass(
        member_name="Test User",
        member_number="KP001",
        status="Aktivno",
        serial_number=expected_serial,
        tenant_id=tenant_id,
    )

    with zipfile.ZipFile(BytesIO(result)) as archive:
        pass_data = json.loads(archive.read("pass.json"))

    # Provera serijskog broja passa.
    assert pass_data["serialNumber"] == expected_serial

    # Provera da je QR poruka generisana za odgovarajućeg tenant-a
    # i serijski broj, umesto statičke poruke "KP001".
    qr_message = pass_data["barcodes"][0]["message"]

    assert qr_message.startswith(f"v1|{tenant_id}|{expected_serial}|")
    assert qr_message != "KP001"

    # Provera da je HMAC potpis u QR poruci validan.
    assert verify_signed_qr_content(qr_message)
