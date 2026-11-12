"""add sequences for ticket types and recipients

Revision ID: 81836b088dbb
Revises: 8a1478d9ad8e
"""

from typing import Sequence, Union

from alembic import op


revision: str = "81836b088dbb"
down_revision: Union[str, Sequence[str], None] = "8a1478d9ad8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE SEQUENCE tip_karte_id_seq
        AS BIGINT START WITH 1 INCREMENT BY 1 NO CYCLE
    """)
    op.execute("""
        ALTER TABLE tip_karte
        ALTER COLUMN id SET DEFAULT nextval('tip_karte_id_seq')
    """)
    op.execute("""
        ALTER SEQUENCE tip_karte_id_seq
        OWNED BY tip_karte.id
    """)

    op.execute("""
        CREATE SEQUENCE primalac_id_seq
        AS BIGINT START WITH 1 INCREMENT BY 1 NO CYCLE
    """)
    op.execute("""
        ALTER TABLE primalac
        ALTER COLUMN id SET DEFAULT nextval('primalac_id_seq')
    """)
    op.execute("""
        ALTER SEQUENCE primalac_id_seq
        OWNED BY primalac.id
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE primalac ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE primalac_id_seq")

    op.execute("ALTER TABLE tip_karte ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE tip_karte_id_seq")
