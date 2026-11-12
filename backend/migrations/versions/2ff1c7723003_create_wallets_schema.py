"""create wallets schema

Revision ID: 2ff1c7723003
Revises: e568b7e083c8
Create Date: 2026-10-01 10:00:54.253248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2ff1c7723003'
down_revision: Union[str, Sequence[str], None] = 'e568b7e083c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the Wallets database schema."""

    op.execute("""
        CREATE TABLE tenant (
            id BIGINT PRIMARY KEY,
            name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    """)

    op.execute("""
        CREATE TABLE korisnik (
            id BIGINT PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            CONSTRAINT fk_korisnik_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES tenant(id)
        )
    """)

    op.execute("""
        CREATE TABLE program (
            id BIGINT PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL,
            CONSTRAINT fk_program_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES tenant(id)
        )
    """)

    op.execute("""
        CREATE TABLE tip_karte (
            id BIGINT PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            program_id BIGINT NOT NULL,
            name TEXT NOT NULL,
            price NUMERIC NOT NULL,
            currency TEXT NOT NULL,
            quantity_limit BIGINT,
            sale_start TIMESTAMP,
            sale_end TIMESTAMP,
            created_at TIMESTAMP NOT NULL,
            CONSTRAINT fk_tip_karte_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES tenant(id),
            CONSTRAINT fk_tip_karte_program
                FOREIGN KEY (program_id)
                REFERENCES program(id)
        )
    """)

    op.execute("""
        CREATE TABLE primalac (
            id BIGINT PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            CONSTRAINT fk_primalac_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES tenant(id)
        )
    """)

    op.execute("""
        CREATE TABLE pass (
            id BIGINT PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            ticket_type_id BIGINT NOT NULL,
            recipient_id BIGINT NOT NULL,
            serial_number TEXT NOT NULL UNIQUE,
            status TEXT NOT NULL,
            issued_at TIMESTAMP NOT NULL,
            valid_from TIMESTAMP,
            valid_until TIMESTAMP,
            created_at TIMESTAMP NOT NULL,
            CONSTRAINT fk_pass_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES tenant(id),
            CONSTRAINT fk_pass_ticket_type
                FOREIGN KEY (ticket_type_id)
                REFERENCES tip_karte(id),
            CONSTRAINT fk_pass_recipient
                FOREIGN KEY (recipient_id)
                REFERENCES primalac(id),
            CONSTRAINT ck_pass_status
                CHECK (
                    status IN (
                        'poslat',
                        'otvoren',
                        'instaliran',
                        'uklonjen',
                        'skeniran',
                        'poništen'
                    )
                )
        )
    """)

    op.execute("""
        CREATE TABLE registracija_uredjaja (
            id BIGINT PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            device_identifier TEXT NOT NULL,
            name TEXT NOT NULL,
            registered_at TIMESTAMP NOT NULL,
            revoked_at TIMESTAMP,
            CONSTRAINT fk_registracija_uredjaja_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES tenant(id)
        )
    """)

    op.execute("""
        CREATE TABLE skeniranje (
            id BIGINT PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            pass_id BIGINT NOT NULL,
            device_registration_id BIGINT NOT NULL,
            user_id BIGINT NOT NULL,
            result TEXT NOT NULL,
            method TEXT NOT NULL,
            scanned_at TIMESTAMP NOT NULL,
            CONSTRAINT fk_skeniranje_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES tenant(id),
            CONSTRAINT fk_skeniranje_pass
                FOREIGN KEY (pass_id)
                REFERENCES pass(id),
            CONSTRAINT fk_skeniranje_device
                FOREIGN KEY (device_registration_id)
                REFERENCES registracija_uredjaja(id),
            CONSTRAINT fk_skeniranje_user
                FOREIGN KEY (user_id)
                REFERENCES korisnik(id),
            CONSTRAINT ck_skeniranje_result
                CHECK (
                    result IN (
                        'VAŽI',
                        'NE POSTOJI',
                        'VEĆ OČITANA',
                        'ISTEKLA',
                        'PONIŠTENA'
                    )
                )
        )
    """)

    op.execute("""
        CREATE INDEX ix_korisnik_tenant_id
        ON korisnik (tenant_id)
    """)

    op.execute("""
        CREATE INDEX ix_program_tenant_id
        ON program (tenant_id)
    """)

    op.execute("""
        CREATE INDEX ix_tip_karte_tenant_id
        ON tip_karte (tenant_id)
    """)

    op.execute("""
        CREATE INDEX ix_primalac_tenant_id
        ON primalac (tenant_id)
    """)

    op.execute("""
        CREATE INDEX ix_pass_tenant_id
        ON pass (tenant_id)
    """)

    op.execute("""
        CREATE INDEX ix_registracija_uredjaja_tenant_id
        ON registracija_uredjaja (tenant_id)
    """)

    op.execute("""
        CREATE INDEX ix_skeniranje_tenant_id
        ON skeniranje (tenant_id)
    """)


def downgrade() -> None:
    """Drop the Wallets database schema."""

    op.execute("DROP TABLE skeniranje")
    op.execute("DROP TABLE registracija_uredjaja")
    op.execute("DROP TABLE pass")
    op.execute("DROP TABLE primalac")
    op.execute("DROP TABLE tip_karte")
    op.execute("DROP TABLE program")
    op.execute("DROP TABLE korisnik")
    op.execute("DROP TABLE tenant")