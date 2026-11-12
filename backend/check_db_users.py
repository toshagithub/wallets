from app.config.settings import settings
from sqlalchemy.engine import make_url

print("DATABASE user:", make_url(settings.database_url).username)
print("MIGRATION user:", make_url(settings.migration_database_url).username)
