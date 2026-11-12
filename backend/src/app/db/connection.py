from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg import Connection

from app.config.settings import settings


@contextmanager
def tenant_connection(tenant_id: int):
    with psycopg.connect(settings.database_url) as connection:
        connection.execute(
            "SELECT set_config('app.tenant_id', %s, true)",
            (str(tenant_id),),
        )

        yield connection


def get_connection(tenant_id: int) -> Generator[Connection, None, None]:
    with tenant_connection(tenant_id) as connection:
        yield connection
