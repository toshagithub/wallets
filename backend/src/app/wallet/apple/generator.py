import hashlib
import json
import shutil
import subprocess
import tempfile
import secrets
from pathlib import Path
from app.wallet.qr import generate_signed_qr_content
from app.config.secrets import load_apple_private_key


BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "template"

SIGNER_CERT = Path("/home/djordje/apple-wallet-pass/certs/pass-3.cer")
WWDR_CERT = Path("/home/djordje/apple-wallet-pass/certs/AppleWWDRCAG4.cer")



def generate_apple_pass(
    member_name: str,
    member_number: str,
    status: str,
    serial_number: str,
    tenant_id: int,
) -> bytes:
    """
    Generiše Apple .pkpass fajl za MVP.

    Podaci se trenutno prosleđuju direktno funkciji.
    Baza i API dolaze u sledećem koraku.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        pass_dir = Path(temp_dir) / "pass"
        pass_dir.mkdir()

        # 1. Kopiranje template fajlova
        for file_path in TEMPLATE_DIR.iterdir():
            if file_path.is_file():
                shutil.copy2(file_path, pass_dir / file_path.name)

        pass_json_path = pass_dir / "pass.json"

        # 2. Učitavanje i popunjavanje pass.json
        with pass_json_path.open("r", encoding="utf-8") as file:
            pass_data = json.load(file)

        authentication_token = secrets.token_urlsafe(32)

        pass_data["serialNumber"] = serial_number
        pass_data["authenticationToken"] = authentication_token
        pass_data["barcodes"][0]["message"] = generate_signed_qr_content(
            tenant_id=tenant_id,
            serial_number=serial_number,
        )

        pass_data["generic"]["primaryFields"][0]["value"] = member_name
        pass_data["generic"]["secondaryFields"][0]["value"] = member_number
        pass_data["generic"]["secondaryFields"][1]["value"] = status

        with pass_json_path.open("w", encoding="utf-8") as file:
            json.dump(
                pass_data,
                file,
                indent=2,
                ensure_ascii=False,
            )

        # 3. Manifest
        manifest = {}

        for file_path in pass_dir.iterdir():
            if file_path.is_file():
                sha1 = hashlib.sha1()

                with file_path.open("rb") as file:
                    while chunk := file.read(8192):
                        sha1.update(chunk)

                manifest[file_path.name] = sha1.hexdigest()

        manifest_path = pass_dir / "manifest.json"

        with manifest_path.open("w", encoding="utf-8") as file:
            json.dump(manifest, file, indent=2)

        # 4. Učitavanje zaštićenog private key-a
        private_key = load_apple_private_key()

        # 5. Privremeni plaintext key samo tokom signing operacije
        with tempfile.NamedTemporaryFile(
            mode="wb",
            suffix=".key",
        ) as key_file:
            key_file.write(private_key)
            key_file.flush()

            signature_path = pass_dir / "signature"

            subprocess.run(
                [
                    "openssl",
                    "smime",
                    "-binary",
                    "-sign",
                    "-signer",
                    str(SIGNER_CERT),
                    "-inkey",
                    key_file.name,
                    "-certfile",
                    str(WWDR_CERT),
                    "-in",
                    str(manifest_path),
                    "-out",
                    str(signature_path),
                    "-outform",
                    "DER",
                ],
                check=True,
                capture_output=True,
                text=True,
            )

        # 6. Pakovanje u .pkpass
        output_path = Path(temp_dir) / f"{serial_number}.pkpass"

        subprocess.run(
            [
                "zip",
                "-q",
                "-j",
                str(output_path),
                str(pass_dir / "icon.png"),
                str(pass_dir / "manifest.json"),
                str(pass_dir / "pass.json"),
                str(pass_dir / "signature"),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        return output_path.read_bytes()
