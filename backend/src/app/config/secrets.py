from pathlib import Path

from cryptography.hazmat.primitives import serialization

from app.config.settings import settings


def load_apple_private_key() -> bytes:
    key_path = Path(settings.apple_private_key_path)

    encrypted_key = key_path.read_bytes()

    private_key = serialization.load_pem_private_key(
        encrypted_key,
        password=settings.apple_private_key_password.encode(),
    )

    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
