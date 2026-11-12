from types import SimpleNamespace

from app.wallet.google import generator
from app.wallet.qr import verify_signed_qr_content


def test_google_pass_uses_serial_number_and_signed_qr(monkeypatch):
    tenant_id = 7
    serial_number = "AB-2026-000123-4"
    inserted_objects = []

    class FakeRequest:
        def __init__(self, response):
            self.response = response

        def execute(self):
            return self.response

    class FakeGenericClass:
        def get(self, resourceId):
            return FakeRequest({"id": resourceId})

    class FakeGenericObject:
        def insert(self, body):
            inserted_objects.append(body)
            return FakeRequest({"id": body["id"]})

    fake_service = SimpleNamespace(
        genericclass=lambda: FakeGenericClass(),
        genericobject=lambda: FakeGenericObject(),
    )

    fake_credentials = SimpleNamespace(
        service_account_email="test@example.com",
        signer=object(),
    )

    monkeypatch.setattr(
        generator.service_account.Credentials,
        "from_service_account_file",
        lambda *args, **kwargs: fake_credentials,
    )
    monkeypatch.setattr(
        generator,
        "build",
        lambda *args, **kwargs: fake_service,
    )
    monkeypatch.setattr(
        generator.jwt,
        "encode",
        lambda signer, payload: b"fake-jwt",
    )

    save_url = generator.generate_google_wallet_pass(
        tenant_id=tenant_id,
        serial_number=serial_number,
    )

    assert len(inserted_objects) == 1
    wallet_object = inserted_objects[0]

    assert wallet_object["id"].endswith(f"wallets_{tenant_id}_{serial_number}")
    assert wallet_object["header"]["defaultValue"]["value"] == serial_number
    assert wallet_object["textModulesData"][0]["body"] == serial_number

    qr_content = wallet_object["barcode"]["value"]
    assert qr_content.startswith(f"v1|{tenant_id}|{serial_number}|")
    assert verify_signed_qr_content(qr_content)

    assert save_url == "https://pay.google.com/gp/v/save/fake-jwt"
