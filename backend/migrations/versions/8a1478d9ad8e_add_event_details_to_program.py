
"""add event details to program

Revision ID: 8a1478d9ad8e
Revises: 7a1c9d4e2f60
"""

from typing import Sequence, Union

from alembic import op


revision: str = "8a1478d9ad8e"
down_revision: Union[str, Sequence[str], None] = "7a1c9d4e2f60"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE program
            ADD COLUMN event_date DATE,
            ADD COLUMN event_time TIME,
            ADD COLUMN location TEXT,
            ADD COLUMN capacity BIGINT,
            ADD COLUMN description TEXT,
            ADD COLUMN image_url TEXT,
            ADD CONSTRAINT ck_program_capacity_positive
                CHECK (capacity IS NULL OR capacity > 0)
    """)

    op.execute("""
        CREATE SEQUENCE program_id_seq
        AS BIGINT
        START WITH 1
        INCREMENT BY 1
        NO CYCLE
    """)

    op.execute("""
        ALTER TABLE program
        ALTER COLUMN id SET DEFAULT nextval('program_id_seq')
    """)

    op.execute("""
        ALTER SEQUENCE program_id_seq
        OWNED BY program.id
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE program
        ALTER COLUMN id DROP DEFAULT
    """)

    op.execute("DROP SEQUENCE program_id_seq")

    op.execute("""
        ALTER TABLE program
            DROP CONSTRAINT ck_program_capacity_positive,
            DROP COLUMN image_url,
            DROP COLUMN description,
            DROP COLUMN capacity,
            DROP COLUMN location,
            DROP COLUMN event_time,
            DROP COLUMN event_date
    """)
