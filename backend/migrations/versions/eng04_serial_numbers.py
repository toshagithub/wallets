
from alembic import op

revision = "eng04_serial_numbers"
down_revision = "f13e8f6b312d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE public.tenant
        ADD COLUMN code VARCHAR(3)
    """)

    op.execute("""
        ALTER TABLE public.tenant
        ADD CONSTRAINT tenant_code_format
        CHECK (code IS NULL OR code ~ '^[A-Z]{2,3}$')
    """)

    op.execute("""
        CREATE UNIQUE INDEX uq_tenant_code
        ON public.tenant (code)
        WHERE code IS NOT NULL
    """)

    op.execute("""
        CREATE TABLE public.pass_serial_counter (
            tenant_id BIGINT NOT NULL
                REFERENCES public.tenant(id),
            issue_year INTEGER NOT NULL,
            last_value INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (tenant_id, issue_year),
            CHECK (issue_year BETWEEN 2000 AND 9999),
            CHECK (last_value BETWEEN 0 AND 999999)
        )
    """)

    op.execute("""
        ALTER TABLE public.pass_serial_counter
        ENABLE ROW LEVEL SECURITY
    """)

    op.execute("""
        ALTER TABLE public.pass_serial_counter
        FORCE ROW LEVEL SECURITY
    """)

    op.execute("""
        CREATE POLICY pass_serial_counter_tenant_isolation
        ON public.pass_serial_counter
        USING (
            current_setting('app.tenant_id', true) IS NOT NULL
            AND tenant_id = current_setting('app.tenant_id', true)::BIGINT
        )
        WITH CHECK (
            current_setting('app.tenant_id', true) IS NOT NULL
            AND tenant_id = current_setting('app.tenant_id', true)::BIGINT
        )
    """)


def downgrade() -> None:
    op.execute("""
        DROP POLICY IF EXISTS pass_serial_counter_tenant_isolation
        ON public.pass_serial_counter
    """)

    op.execute("DROP TABLE public.pass_serial_counter")
    op.execute("DROP INDEX public.uq_tenant_code")

    op.execute("""
        ALTER TABLE public.tenant
        DROP CONSTRAINT tenant_code_format
    """)

    op.execute("""
        ALTER TABLE public.tenant
        DROP COLUMN code
    """)
