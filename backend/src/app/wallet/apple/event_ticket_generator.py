import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from app.config.settings import settings

from app.config.secrets import load_apple_private_key
from app.wallet.apple.event_ticket import map_canonical_ticket_to_apple
from app.wallet.qr import generate_signed_qr_content


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "template"

SIGNER_CERT = Path("/home/djordje/apple-wallet-pass/certs/pass-3.cer")
WWDR_CERT = Path("/home/djordje/apple-wallet-pass/certs/AppleWWDRCAG4.cer")

def generate_apple_event_ticket(
    canonical_data: dict[str, Any],
    authentication_token: str,
) -> bytes:
    """Generate a signed Apple Wallet event ticket (.pkpass)."""
    pass_data = map_canonical_ticket_to_apple(
        canonical_data,
        authentication_token,
    )

    tenant_id = canonical_data["tenant"]["id"]
    serial_number = canonical_data["pass"]["serial_number"]

    pass_data["barcodes"][0]["message"] = generate_signed_qr_content(
        tenant_id=tenant_id,
        serial_number=serial_number,
    )

    with tempfile.TemporaryDirectory() as temp_dir:
        pass_dir = Path(temp_dir) / "pass"
        pass_dir.mkdir()

        shutil.copy2(TEMPLATE_DIR / "icon.png", pass_dir / "icon.png")

        pass_json_path = pass_dir / "pass.json"
        with pass_json_path.open("w", encoding="utf-8") as file:
            json.dump(pass_data, file, indent=2, ensure_ascii=False)

        manifest = {}
        for file_path in pass_dir.iterdir():
            if file_path.is_file():
                manifest[file_path.name] = hashlib.sha1(
                    file_path.read_bytes()
                ).hexdigest()

        manifest_path = pass_dir / "manifest.json"
        with manifest_path.open("w", encoding="utf-8") as file:
            json.dump(manifest, file, indent=2)

        private_key = load_apple_private_key()
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".key") as key_file:
            key_file.write(private_key)
            key_file.flush()

            signature_path = pass_dir / "signature"
            subprocess.run(
                [
                    "openssl", "smime", "-binary", "-sign",
                    "-signer", str(SIGNER_CERT),
                    "-inkey", key_file.name,
                    "-certfile", str(WWDR_CERT),
                    "-in", str(manifest_path),
                    "-out", str(signature_path),
                    "-outform", "DER",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        output_path = Path(temp_dir) / f"{serial_number}.pkpass"
        subprocess.run(
            [
                "zip", "-q", "-j", str(output_path),
                str(pass_dir / "icon.png"),
                str(pass_dir / "manifest.json"),
                str(pass_json_path),
                str(pass_dir / "signature"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        return output_path.read_bytes()
