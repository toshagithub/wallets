
import json
import zipfile
from io import BytesIO
from pathlib import Path

from app.wallet.apple import event_ticket_generator as generator
from app.wallet.qr import verify_signed_qr_content


EXAMPLE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "app"
    / "wallet"
    / "canonical"
    / "example.json"
)

def test_generates_event_ticket_package(monkeypatch):
    canonical_data = json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))

    monkeypatch.setattr(
        generator.settings,
        "apple_web_service_url",
        "https://wallet.example.test/apple-wallet",
    )

    # Testiramo strukturu paketa, bez stvarnog Apple potpisivanja.
    def fake_subprocess_run(args, **kwargs):
        if args[0] == "openssl":
            output_path = Path(args[args.index("-out") + 1])
            output_path.write_bytes(b"test-signature")
        elif args[0] == "zip":
            output_path = Path(args[3])
            pass_dir = Path(args[-1]).parent

            with zipfile.ZipFile(output_path, "w") as archive:
                for name in ("icon.png", "manifest.json", "pass.json", "signature"):
                    archive.write(pass_dir / name, name)

    monkeypatch.setattr(generator.subprocess, "run", fake_subprocess_run)
    monkeypatch.setattr(
        generator,
        "load_apple_private_key",
        lambda: b"test-private-key",
    )

    authentication_token = "test-authentication-token"

    result = generator.generate_apple_event_ticket(
        canonical_data,
        authentication_token,
    )

    with zipfile.ZipFile(BytesIO(result)) as archive:
        names = set(archive.namelist())
        pass_data = json.loads(archive.read("pass.json"))
        manifest = json.loads(archive.read("manifest.json"))

    assert {"icon.png", "manifest.json", "pass.json", "signature"} <= names
    assert pass_data["serialNumber"] == canonical_data["pass"]["serial_number"]
    assert pass_data["eventTicket"]["primaryFields"][0]["value"] == "Demo koncert"
    assert pass_data["authenticationToken"] == authentication_token
    assert pass_data["webServiceURL"] == "https://wallet.example.test/apple-wallet"

    qr_message = pass_data["barcodes"][0]["message"]
    assert qr_message.startswith(
        f"v1|{canonical_data['tenant']['id']}|"
        f"{canonical_data['pass']['serial_number']}|"
    )
    assert verify_signed_qr_content(qr_message)

    assert set(manifest) == {"icon.png", "pass.json"}
