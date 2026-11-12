from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

import psycopg

from app.config.settings import settings


password_hasher = PasswordHasher()


def authenticate_user(email: str, password: str) -> dict | None:
    with psycopg.connect(settings.database_url) as connection:
        with connection.transaction():
            connection.execute(
                "SELECT set_config('app.login_email', %s, true)",
                (email.strip().lower(),),
            )
            user = connection.execute(
                """
                SELECT id, tenant_id, email, name, password_hash
                FROM public.korisnik
                WHERE email = %s
                """,
                (email.strip().lower(),),
            ).fetchone()

    if user is None:
        return None

    try:
        password_hasher.verify(user[4], password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return None

    return {
        "id": user[0],
        "tenant_id": user[1],
        "email": user[2],
        "name": user[3],
    }
