import pytest

from app.services.pass_email_content import (
    build_apple_pass_email,
    build_both_pass_email,
    build_google_pass_email,
)


@pytest.fixture
def canonical_data():
    return {
        "event": {
            "name": "Konferencija 2026",
            "starts_at": "2026-12-15T18:30:00+00:00",
            "ends_at": "2026-12-15T22:00:00+00:00",
            "location": "Beograd",
        }
    }


def test_build_apple_pass_email(canonical_data):
    result = build_apple_pass_email(canonical_data)

    assert result["subject"] == "Konferencija 2026 – 15.12.2026. – Vaša digitalna ulaznica"
    assert "Konferencija 2026" in result["text_body"]
    assert "15.12.2026. u 18:30" in result["text_body"]
    assert "Beograd" in result["text_body"]
    assert "Apple Wallet" in result["text_body"]
    assert "Konferencija 2026" in result["html_body"]
    assert "Wallets tim" in result["html_body"]


def test_build_google_pass_email(canonical_data):
    save_url = "https://pay.google.com/gp/v/save/test-token"

    result = build_google_pass_email(canonical_data, save_url)

    assert result["subject"] == "Konferencija 2026 – 15.12.2026. – Vaša digitalna ulaznica"
    assert save_url in result["text_body"]
    assert save_url in result["html_body"]
    assert "Dodaj u Google Wallet" in result["html_body"]
    assert "Konferencija 2026" in result["text_body"]


def test_build_both_pass_email(canonical_data):
    save_url = "https://pay.google.com/gp/v/save/test-token"

    result = build_both_pass_email(canonical_data, save_url)

    assert result["subject"] == "Konferencija 2026 – 15.12.2026. – Vaše digitalne ulaznice"
    assert save_url in result["text_body"]
    assert save_url in result["html_body"]
    assert "Dodaj u Google Wallet" in result["html_body"]
    assert "Apple Wallet" in result["text_body"]
    assert ".pkpass" in result["text_body"]
    assert "Apple Wallet" in result["html_body"]
    assert "Konferencija 2026" in result["html_body"]


def test_email_content_escapes_html(canonical_data):
    canonical_data["event"]["name"] = "Konferencija <2026>"

    result = build_apple_pass_email(canonical_data)

    assert "Konferencija &lt;2026&gt;" in result["html_body"]


def test_google_email_requires_save_url(canonical_data):
    with pytest.raises(ValueError, match="Google Wallet link nije naveden"):
        build_google_pass_email(canonical_data, "")


def test_both_email_requires_save_url(canonical_data):
    with pytest.raises(ValueError, match="Google Wallet link nije naveden"):
        build_both_pass_email(canonical_data, "")
