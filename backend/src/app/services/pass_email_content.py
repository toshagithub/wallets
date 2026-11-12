from datetime import datetime
from html import escape


def _event_details(canonical_data: dict) -> tuple[str, str, str]:
    event = canonical_data["event"]

    starts_at = datetime.fromisoformat(event["starts_at"])
    event_date = starts_at.strftime("%d.%m.%Y.")
    event_time = starts_at.strftime("%H:%M")

    return (
        str(event["name"]),
        f"{event_date} u {event_time}",
        str(event.get("location") or "Nije navedena"),
    )


def _email_subject(
    event_name: str,
    starts_at: str,
    plural: bool = False,
) -> str:
    event_date = datetime.fromisoformat(starts_at).strftime("%d.%m.%Y.")
    ticket_text = (
        "Vaše digitalne ulaznice"
        if plural
        else "Vaša digitalna ulaznica"
    )
    return f"{event_name} – {event_date} – {ticket_text}"


def build_apple_pass_email(canonical_data: dict) -> dict[str, str]:
    event_name, event_datetime, location = _event_details(canonical_data)

    text_body = (
        "Poštovani,\\n\\n"
        f"Vaša digitalna ulaznica za događaj {event_name} "
        "uspešno je izdata.\\n\\n"
        "Informacije o događaju:\\n"
        f"Događaj: {event_name}\\n"
        f"Datum: {event_datetime}\\n"
        f"Lokacija: {location}\\n\\n"
        "U prilogu ove poruke nalazi se vaša digitalna ulaznica.\\n\\n"
        "Da biste je dodali u Apple Wallet, otvorite priloženi "
        "fajl na svom iPhone uređaju i pratite ponuđene korake.\\n\\n"
        "Vidimo se na događaju!\\n\\n"
        "Srdačan pozdrav,\\n"
        "Wallets tim"
    )

    html_body = f"""
    <!DOCTYPE html>
    <html lang="sr">
    <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
        <p>Poštovani,</p>

        <p>
            Vaša digitalna ulaznica za događaj
            <strong>{escape(event_name)}</strong> uspešno je izdata.
        </p>

        <h3>Informacije o događaju:</h3>
        <ul>
            <li><strong>Događaj:</strong> {escape(event_name)}</li>
            <li><strong>Datum:</strong> {escape(event_datetime)}</li>
            <li><strong>Lokacija:</strong> {escape(location)}</li>
        </ul>

        <p>U prilogu ove poruke nalazi se vaša digitalna ulaznica.</p>

        <p>
            Da biste je dodali u Apple Wallet, otvorite priloženi
            fajl na svom iPhone uređaju i pratite ponuđene korake.
        </p>

        <p>Vidimo se na događaju!</p>

        <p>Srdačan pozdrav,<br><strong>Wallets tim</strong></p>
    </body>
    </html>
    """

    return {
        "subject": _email_subject(event_name, canonical_data["event"]["starts_at"]),
        "text_body": text_body,
        "html_body": html_body,
    }


def build_google_pass_email(
    canonical_data: dict,
    save_url: str,
) -> dict[str, str]:
    if not save_url:
        raise ValueError("Google Wallet link nije naveden.")

    event_name, event_datetime, location = _event_details(canonical_data)

    text_body = (
        "Poštovani,\\n\\n"
        f"Vaša digitalna ulaznica za događaj {event_name} "
        "uspešno je izdata.\\n\\n"
        "Informacije o događaju:\\n"
        f"Događaj: {event_name}\\n"
        f"Datum: {event_datetime}\\n"
        f"Lokacija: {location}\\n\\n"
        "Dodajte ulaznicu u Google Wallet putem sledećeg linka:\\n"
        f"{save_url}\\n\\n"
        "Vidimo se na događaju!\\n\\n"
        "Srdačan pozdrav,\\n"
        "Wallets tim"
    )

    safe_url = escape(save_url, quote=True)

    html_body = f"""
    <!DOCTYPE html>
    <html lang="sr">
    <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
        <p>Poštovani,</p>

        <p>
            Vaša digitalna ulaznica za događaj
            <strong>{escape(event_name)}</strong> uspešno je izdata.
        </p>

        <h3>Informacije o događaju:</h3>
        <ul>
            <li><strong>Događaj:</strong> {escape(event_name)}</li>
            <li><strong>Datum:</strong> {escape(event_datetime)}</li>
            <li><strong>Lokacija:</strong> {escape(location)}</li>
        </ul>

        <p>
            Kliknite na dugme ispod kako biste dodali ulaznicu
            u Google Wallet.
        </p>

        <p>
            <a href="{safe_url}"
               style="display: inline-block; padding: 12px 20px;
                      background-color: #1a73e8; color: #ffffff;
                      text-decoration: none; border-radius: 5px;">
                Dodaj u Google Wallet
            </a>
        </p>

        <p>Vidimo se na događaju!</p>

        <p>Srdačan pozdrav,<br><strong>Wallets tim</strong></p>
    </body>
    </html>
    """

    return {
        "subject": _email_subject(event_name, canonical_data["event"]["starts_at"]),
        "text_body": text_body,
        "html_body": html_body,
    }


def build_both_pass_email(
    canonical_data: dict,
    save_url: str,
) -> dict[str, str]:
    if not save_url:
        raise ValueError("Google Wallet link nije naveden.")

    event_name, event_datetime, location = _event_details(canonical_data)
    safe_url = escape(save_url, quote=True)

    text_body = (
        "Poštovani,\\n\\n"
        f"Vaša digitalna ulaznica za događaj {event_name} "
        "uspešno je izdata.\\n\\n"
        "Informacije o događaju:\\n"
        f"Događaj: {event_name}\\n"
        f"Datum: {event_datetime}\\n"
        f"Lokacija: {location}\\n\\n"
        "Google Wallet: Dodajte ulaznicu putem sledećeg linka:\\n"
        f"{save_url}\\n\\n"
        "Apple Wallet: Ulaznica se nalazi u prilogu ove poruke. "
        "Otvorite priloženi .pkpass fajl na iPhone uređaju "
        "i pratite ponuđene korake.\\n\\n"
        "Vidimo se na događaju!\\n\\n"
        "Srdačan pozdrav,\\n"
        "Wallets tim"
    )

    html_body = f"""
    <!DOCTYPE html>
    <html lang="sr">
    <body style="font-family: Arial, sans-serif; color: #222; line-height: 1.6;">
        <p>Poštovani,</p>

        <p>
            Vaša digitalna ulaznica za događaj
            <strong>{escape(event_name)}</strong> uspešno je izdata.
        </p>

        <h3>Informacije o događaju:</h3>
        <ul>
            <li><strong>Događaj:</strong> {escape(event_name)}</li>
            <li><strong>Datum:</strong> {escape(event_datetime)}</li>
            <li><strong>Lokacija:</strong> {escape(location)}</li>
        </ul>

        <h3>Google Wallet</h3>
        <p>Kliknite na dugme ispod kako biste dodali ulaznicu u Google Wallet.</p>
        <p>
            <a href="{safe_url}"
               style="display: inline-block; padding: 12px 20px;
                      background-color: #1a73e8; color: #ffffff;
                      text-decoration: none; border-radius: 5px;">
                Dodaj u Google Wallet
            </a>
        </p>

        <h3>Apple Wallet</h3>
        <p>
            Ulaznica se nalazi u prilogu ove poruke.
            Otvorite priloženi .pkpass fajl na iPhone uređaju
            i pratite ponuđene korake.
        </p>

        <p>Vidimo se na događaju!</p>

        <p>Srdačan pozdrav,<br><strong>Wallets tim</strong></p>
    </body>
    </html>
    """

    return {
        "subject": _email_subject(
            event_name,
            canonical_data["event"]["starts_at"],
            plural=True,
        ),
        "text_body": text_body,
        "html_body": html_body,
    }
