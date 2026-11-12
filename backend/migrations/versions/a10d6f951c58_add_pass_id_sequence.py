"""add pass ID sequence

Revision ID: a10d6f951c58
Revises: 84cdbe83b57f
"""
from typing import Sequence, Union

from alembic import op

revision: str = "a10d6f951c58"
down_revision: Union[str, Sequence[str], None] = "84cdbe83b57f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE pass_id_seq OWNED BY pass.id")
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
    op.execute("ALTER TABLE pass ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE pass_id_seq")
