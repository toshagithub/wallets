
"""force tenant row level security

Revision ID: 8600fcf8dbf8
Revises: eng04_serial_numbers
"""

from typing import Sequence, Union

from alembic import op


revision: str = "8600fcf8dbf8"
down_revision: Union[str, Sequence[str], None] = "eng04_serial_numbers"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TENANT_TABLES = (
    "korisnik",
    "program",
    "tip_karte",
    "primalac",
    "pass",
    "registracija_uredjaja",
    "skeniranje",
)


def upgrade() -> None:
    """Force RLS policies for tenant-owned tables."""
    for table in TENANT_TABLES:
        op.execute(
            f"ALTER TABLE public.{table} FORCE ROW LEVEL SECURITY"
        )


def downgrade() -> None:
    """Remove forced RLS while keeping RLS enabled."""
    for table in reversed(TENANT_TABLES):
        op.execute(
            f"ALTER TABLE public.{table} NO FORCE ROW LEVEL SECURITY"
        )
