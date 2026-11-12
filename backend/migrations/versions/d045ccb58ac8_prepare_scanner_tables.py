"""Prepare scanner tables.

Revision ID: d045ccb58ac8
Revises: 9b7c2d1e4a60
"""

from typing import Sequence, Union

from alembic import op


revision: str = "d045ccb58ac8"
down_revision: Union[str, Sequence[str], None] = "9b7c2d1e4a60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE SEQUENCE registracija_uredjaja_id_seq
        AS BIGINT START WITH 1 INCREMENT BY 1 NO CYCLE
    """)
    op.execute("""
        SELECT setval(
            'registracija_uredjaja_id_seq',
            COALESCE((SELECT MAX(id) FROM registracija_uredjaja), 0) + 1,
            false
        )
    """)
    op.execute("""
        ALTER TABLE registracija_uredjaja
        ALTER COLUMN id SET DEFAULT nextval('registracija_uredjaja_id_seq')
    """)
    op.execute("""
        ALTER SEQUENCE registracija_uredjaja_id_seq
        OWNED BY registracija_uredjaja.id
    """)

    op.execute("""
        CREATE SEQUENCE skeniranje_id_seq
        AS BIGINT START WITH 1 INCREMENT BY 1 NO CYCLE
    """)
    op.execute("""
        SELECT setval(
            'skeniranje_id_seq',
            COALESCE((SELECT MAX(id) FROM skeniranje), 0) + 1,
            false
        )
    """)
    op.execute("""
        ALTER TABLE skeniranje
        ALTER COLUMN id SET DEFAULT nextval('skeniranje_id_seq')
    """)
    op.execute("""
        ALTER SEQUENCE skeniranje_id_seq
        OWNED BY skeniranje.id
    """)

    op.execute("""
        ALTER TABLE skeniranje
        ALTER COLUMN pass_id DROP NOT NULL
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE skeniranje
        ALTER COLUMN pass_id SET NOT NULL
    """)
    op.execute("""
        ALTER TABLE skeniranje
        ALTER COLUMN id DROP DEFAULT
    """)
    op.execute("DROP SEQUENCE skeniranje_id_seq")
    op.execute("""
        ALTER TABLE registracija_uredjaja
        ALTER COLUMN id DROP DEFAULT
    """)
    op.execute("DROP SEQUENCE registracija_uredjaja_id_seq")
