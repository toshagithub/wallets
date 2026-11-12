from datetime import datetime

import psycopg

from app.config.settings import settings


TENANTS = [
    (1, "Test Tenant A"),
    (2, "Test Tenant B"),
]

USERS = [
    (
        1,
        1,
        "admin.a@wallets.local",
        "Admin A",
        "$argon2id$v=19$m=65536,t=3,p=4$piPxu+NizWZGNV446YIn6A$hZYnoIyGiaDu18y1suVC7E1FWtHQh3vnylwCXbQ1zSs",
    ),
    (
        2,
        1,
        "user.a@wallets.local",
        "User A",
        "$argon2id$v=19$m=65536,t=3,p=4$Td+R2DZeIRH6w6tSX7wskw$Kx2vEQXsXlrROfc5QBKuxis7ZFvbsBWMFcz/UV8xplI",
    ),
    (
        3,
        2,
        "admin.b@wallets.local",
        "Admin B",
        "$argon2id$v=19$m=65536,t=3,p=4$nvL6QrtsUT/DLmTr9RN7EA$smRhaR08zsPStywU1R5i0d+HsoI76z/+Ef/Z5RfkDgo",
    ),
    (
        4,
        2,
        "user.b@wallets.local",
        "User B",
        "$argon2id$v=19$m=65536,t=3,p=4$fkmlRCNaK5O+v6m4j09UMw$EPX1ApqqHGW05freJqHbJfvbGioyiIhjP6OsnVK3/KI",
    ),
    (
        5,
        1,
        "milan.t@wallets.local",
        "Milan",
        "$argon2id$v=19$m=65536,t=3,p=4$tdUcZGNWlHxFohsZAeGBSg$S+BQFnFApdxlnIvBLQ2VEEdenNnTVTf4ub0NqBsAnSk",
    ),
]


with psycopg.connect(settings.database_url) as connection:
    with connection.transaction():
        now = datetime.now()

        for tenant_id, name in TENANTS:
            connection.execute(
                """
                INSERT INTO tenant (id, name, created_at)
                VALUES (%s, %s, %s)
                ON CONFLICT (id) DO NOTHING
                """,
                (tenant_id, name, now),
            )

        for tenant_id in (1, 2):
            connection.execute(
                "SELECT set_config('app.tenant_id', %s, true)",
                (str(tenant_id),),
            )

            for user_id, user_tenant_id, email, name, password_hash in USERS:
                if user_tenant_id != tenant_id:
                    continue

                connection.execute(
                    """
                    INSERT INTO korisnik
                        (id, tenant_id, email, name, password_hash, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO NOTHING
                    """,
                    (
                        user_id,
                        user_tenant_id,
                        email,
                        name,
                        password_hash,
                        now,
                    ),
                )

print("Test users seeded successfully.")
