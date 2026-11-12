from sqlalchemy import create_engine, text
from app.config.settings import settings

engine = create_engine(settings.migration_database_url)

with engine.connect() as connection:
    rows = connection.execute(
        text("""
            SELECT tablename, tableowner
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
    ).fetchall()

    for row in rows:
        print(row)