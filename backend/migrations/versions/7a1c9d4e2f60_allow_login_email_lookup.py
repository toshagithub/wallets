"""allow login lookup by exact email

Revision ID: 7a1c9d4e2f60
Revises: 8600fcf8dbf8
"""

from typing import Sequence, Union

from alembic import op

revision: str = "7a1c9d4e2f60"
down_revision: Union[str, Sequence[str], None] = "8600fcf8dbf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE POLICY korisnik_login_email_lookup
        ON public.korisnik
        FOR SELECT
        USING (
            current_setting('app.login_email', true) IS NOT NULL
            AND email = current_setting('app.login_email', true)
        )
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS korisnik_login_email_lookup
        ON public.korisnik
    """)
