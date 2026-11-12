"""add Apple authentication token to pass

Revision ID: 0b57e7fbb5ee
Revises: 0d532215d02e
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0b57e7fbb5ee"
down_revision: Union[str, Sequence[str], None] = "0d532215d02e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE public.pass
        ADD COLUMN apple_authentication_token TEXT
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE public.pass
        DROP COLUMN apple_authentication_token
    """)
