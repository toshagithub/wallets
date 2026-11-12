from app.services import email as email_service


def test_send_pass_email_with_apple_attachment(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            captured["connection"] = args
            captured["timeout"] = kwargs["timeout"]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def login(self, username, password):
            captured["login"] = (username, password)

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(email_service.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(email_service.settings, "smtp_port", 465)
    monkeypatch.setattr(email_service.settings, "smtp_username", "test@example.com")
    monkeypatch.setattr(email_service.settings, "smtp_password", "test-password")
    monkeypatch.setattr(email_service.settings, "email_from", "test@example.com")
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", FakeSMTP)

    email_service.send_pass_email(
        recipient="guest@example.com",
        subject="Vaša ulaznica",
        text_body="Google Wallet: https://example.com/save/test",
        html_body="<p>Vaša ulaznica</p>",
        attachment_bytes=b"fake-pkpass-content",
        attachment_filename="ticket.pkpass",
    )

    message = captured["message"]

    assert captured["connection"] == ("smtp.test", 465)
    assert captured["timeout"] == 20
    assert captured["login"] == ("test@example.com", "test-password")
    assert message["To"] == "guest@example.com"
    assert message["Subject"] == "Vaša ulaznica"

    parts = list(message.iter_attachments())
    assert len(parts) == 1
    assert parts[0].get_filename() == "ticket.pkpass"
    assert parts[0].get_content_type() == "application/vnd.apple.pkpass"


def test_send_pass_email_requires_smtp_credentials(monkeypatch):
    monkeypatch.setattr(email_service.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(email_service.settings, "smtp_username", None)
    monkeypatch.setattr(email_service.settings, "smtp_password", None)

    try:
        email_service.send_pass_email(
            recipient="guest@example.com",
            subject="Test",
            text_body="Test",
            html_body="<p>Test</p>",
        )
    except ValueError as error:
        assert str(error) == "SMTP autentifikacija nije konfigurisana."
    else:
        raise AssertionError("Očekivana je ValueError greška.")


def test_send_pass_email_uses_starttls_when_ssl_disabled(monkeypatch):
    captured = {}

    class FakeSMTP:
        def __init__(self, *args, **kwargs):
            captured["connection"] = args
            captured["timeout"] = kwargs["timeout"]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def ehlo(self):
            captured["ehlo"] = captured.get("ehlo", 0) + 1

        def starttls(self, context):
            captured["starttls_context"] = context

        def login(self, username, password):
            captured["login"] = (username, password)

        def send_message(self, message):
            captured["message"] = message

    monkeypatch.setattr(email_service.settings, "smtp_host", "smtp.test")
    monkeypatch.setattr(email_service.settings, "smtp_port", 587)
    monkeypatch.setattr(email_service.settings, "smtp_username", "test@example.com")
    monkeypatch.setattr(email_service.settings, "smtp_password", "test-password")
    monkeypatch.setattr(email_service.settings, "smtp_use_ssl", False)
    monkeypatch.setattr(email_service.settings, "email_from", "test@example.com")
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    def unexpected_ssl(*args, **kwargs):
        raise AssertionError("SMTP_SSL ne treba da se koristi u STARTTLS režimu.")

    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", unexpected_ssl)

    email_service.send_pass_email(
        recipient="guest@example.com",
        subject="STARTTLS test",
        text_body="Test",
        html_body="<p>Test</p>",
    )

    assert captured["connection"] == ("smtp.test", 587)
    assert captured["timeout"] == 20
    assert captured["ehlo"] == 2
    assert captured["starttls_context"] is not None
    assert captured["login"] == ("test@example.com", "test-password")
    assert captured["message"]["To"] == "guest@example.com"
