"""add tenant row level security

Revision ID: fd2bebee5d60
Revises: 2ff1c7723003
Create Date: 2026-10-01
"""

from typing import Sequence, Union

from alembic import op


revision: str = "fd2bebee5d60"
down_revision: Union[str, Sequence[str], None] = "2ff1c7723003"
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
    """Enable tenant isolation with PostgreSQL row-level security."""

    for table in TENANT_TABLES:
        op.execute(
            f"""
            ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;
            """
        )

        op.execute(
            f"""
            CREATE POLICY {table}_tenant_isolation
            ON {table}
            USING (
                current_setting('app.tenant_id', true) IS NOT NULL
                AND tenant_id = current_setting('app.tenant_id', true)::BIGINT
            )
            WITH CHECK (
                current_setting('app.tenant_id', true) IS NOT NULL
                AND tenant_id = current_setting('app.tenant_id', true)::BIGINT
            );
            """
        )


def downgrade() -> None:
    """Disable tenant isolation policies."""

    for table in reversed(TENANT_TABLES):
        op.execute(
            f"""
            DROP POLICY IF EXISTS {table}_tenant_isolation ON {table};
            """
        )

        op.execute(
            f"""
            ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;
            """
        )