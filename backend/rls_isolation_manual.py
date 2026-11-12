from sqlalchemy import create_engine, text
from app.config.settings import settings


engine = create_engine(settings.migration_database_url)

with engine.begin() as connection:
    # 1. Napravi dva testna tenanta.
    tenant_1 = connection.execute(
        text("""
            INSERT INTO tenant (id, name, created_at)
            VALUES (1001, 'RLS Test Tenant 1', CURRENT_TIMESTAMP)
            RETURNING id
        """)
    ).scalar_one()

    tenant_2 = connection.execute(
        text("""
            INSERT INTO tenant (id, name, created_at)
            VALUES (1002, 'RLS Test Tenant 2', CURRENT_TIMESTAMP)
            RETURNING id
        """)
    ).scalar_one()

    # 2. Privremeno isključi RLS samo za tenant tabelu
    #    nije nam potrebna za sam test izolacije.
    #    Testiraćemo tenant-scoped tabelu "program".

    # 3. Ubaci podatke za oba tenanta.
    connection.execute(
        text("""
            INSERT INTO program (id, tenant_id, name, created_at)
            VALUES
                (1001, :tenant_1, 'Program Tenant 1', CURRENT_TIMESTAMP),
                (1002, :tenant_2, 'Program Tenant 2', CURRENT_TIMESTAMP)
        """),
        {
            "tenant_1": tenant_1,
            "tenant_2": tenant_2,
        },
    )

    # 4. Postavi sesiju na tenant 1.
    connection.execute(
        text("SELECT set_config('app.tenant_id', :tenant_id, false)"),
        {"tenant_id": str(tenant_1)},
    )

    rows_tenant_1 = connection.execute(
        text("""
            SELECT id, tenant_id, name
            FROM program
            ORDER BY id
        """)
    ).fetchall()

    print("Tenant 1 vidi:")
    for row in rows_tenant_1:
        print(row)

    # 5. Pokušaj da ubaciš podatak za tenant 2
    #    dok je sesija postavljena na tenant 1.
    try:
        connection.execute(
            text("""
                INSERT INTO program (id, tenant_id, name, created_at)
                VALUES (1003, :tenant_2, 'Nedozvoljeni program', CURRENT_TIMESTAMP)
            """),
            {"tenant_2": tenant_2},
        )
        print("GREŠKA: Tenant 1 je uspeo da upiše podatak Tenant-a 2.")
    except Exception as exc:
        print("INSERT za Tenant 2 odbijen:", type(exc).__name__)

    # 6. Sve se na kraju transakcije automatski rollback-uje.