"""add event end datetime and pass ID sequence

Revision ID: 84cdbe83b57f
Revises: a91c4e7d2b60
Create Date: 2026-10-22 09:17:22.324326
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "84cdbe83b57f"
down_revision: Union[str, Sequence[str], None] = "a91c4e7d2b60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "program",
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.execute("""
        CREATE SEQUENCE pass_id_seq OWNED BY pass.id
    """)
    op.execute("""
        SELECT setval(
            'pass_id_seq',
            COALESCE((SELECT MAX(id) FROM pass), 0) + 1,
            false
        )
    """)
    op.execute("""
        ALTER TABLE pass
        ALTER COLUMN id SET DEFAULT nextval('pass_id_seq'::regclass)
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE pass ALTER COLUMN id DROP DEFAULT
    """)
    op.execute("DROP SEQUENCE pass_id_seq")
    op.drop_column("program", "ends_at")
