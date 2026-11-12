"""link recipients to events

Revision ID: a91c4e7d2b60
Revises: 81836b088dbb
"""

from typing import Sequence, Union

from alembic import op


revision: str = "a91c4e7d2b60"
down_revision: Union[str, Sequence[str], None] = "81836b088dbb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE primalac
        ADD COLUMN program_id BIGINT
        REFERENCES program(id)
    """)

    op.execute("""
        CREATE INDEX ix_primalac_program_id
        ON primalac(program_id)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX ix_primalac_program_id")
    op.execute("ALTER TABLE primalac DROP COLUMN program_id")
