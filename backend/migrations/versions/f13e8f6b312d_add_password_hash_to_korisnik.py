"""add password hash to korisnik

Revision ID: f13e8f6b312d
Revises: fd2bebee5d60
Create Date: 2026-10-05 08:08:40.878913

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f13e8f6b312d'
down_revision: Union[str, Sequence[str], None] = 'fd2bebee5d60'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add password hash to users."""
    op.add_column(
        "korisnik",
        sa.Column("password_hash", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove password hash from users."""
    op.drop_column("korisnik", "password_hash")
