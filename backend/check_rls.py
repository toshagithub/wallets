from sqlalchemy import create_engine, text
from app.config.settings import settings

engine = create_engine(settings.migration_database_url)

with engine.connect() as connection:
    result = connection.execute(
        text("""
            SELECT
                schemaname,
                tablename,
                policyname,
                cmd,
                qual,
                with_check
            FROM pg_policies
            WHERE schemaname = 'public'
            ORDER BY tablename, policyname
        """)
    )

    for row in result:
        print(row)