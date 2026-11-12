from sqlalchemy import create_engine, text
from app.config.settings import settings

engine = create_engine(settings.migration_database_url)

with engine.begin() as connection:
    connection.execute(text("""
        INSERT INTO tenant (id, name, created_at)
        VALUES
            (1001, 'RLS Test Tenant 1', CURRENT_TIMESTAMP),
            (1002, 'RLS Test Tenant 2', CURRENT_TIMESTAMP)
    """))

    connection.execute(text("""
        INSERT INTO program (id, tenant_id, name, created_at)
        VALUES
            (1001, 1001, 'Program Tenant 1', CURRENT_TIMESTAMP),
            (1002, 1002, 'Program Tenant 2', CURRENT_TIMESTAMP)
    """))

print("RLS test podaci su kreirani.")
