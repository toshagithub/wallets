from sqlalchemy import create_engine, text
from app.config.settings import settings

engine = create_engine(settings.migration_database_url)

with engine.begin() as connection:
    connection.execute(
        text("""
            DELETE FROM program
            WHERE id IN (1001, 1002, 1003)
        """)
    )

    connection.execute(
        text("""
            DELETE FROM tenant
            WHERE id IN (1001, 1002)
        """)
    )

print("RLS test podaci su obrisani.")