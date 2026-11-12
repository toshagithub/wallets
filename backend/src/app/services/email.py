import smtplib
import ssl
from email.message import EmailMessage

from app.config.settings import settings


def send_pass_email(
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str,
    attachment_bytes: bytes | None = None,
    attachment_filename: str | None = None,
) -> None:
    if not settings.smtp_host:
        raise ValueError("SMTP host nije konfigurisan.")

    if not settings.smtp_username or not settings.smtp_password:
        raise ValueError("SMTP autentifikacija nije konfigurisana.")

    if not recipient:
        raise ValueError("Email primaoca nije naveden.")

    if attachment_bytes is not None and not attachment_filename:
        raise ValueError("Naziv email priloga nije naveden.")

    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = recipient
    message["Subject"] = subject

    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    if attachment_bytes is not None:
        message.add_attachment(
            attachment_bytes,
            maintype="application",
            subtype="vnd.apple.pkpass",
            filename=attachment_filename,
        )

    context = ssl.create_default_context()

    if settings.smtp_use_ssl:
        smtp_connection = smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            context=context,
            timeout=20,
        )
    else:
        smtp_connection = smtplib.SMTP(
            settings.smtp_host,
            settings.smtp_port,
            timeout=20,
        )

    with smtp_connection as smtp:
        if not settings.smtp_use_ssl:
            smtp.ehlo()
            smtp.starttls(context=context)
            smtp.ehlo()

        smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
