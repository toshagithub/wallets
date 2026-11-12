from datetime import date

from psycopg import Connection


def calculate_check_digit(issue_year: int, sequence: int) -> str:
    if not 2000 <= issue_year <= 9999:
        raise ValueError("Godina mora biti između 2000 i 9999.")

    if not 1 <= sequence <= 999999:
        raise ValueError("Redni broj mora biti između 1 i 999999.")

    digits = f"{issue_year:04d}{sequence:06d}"
    weights = (2, 3, 4, 5, 6, 7)

    total = sum(
        int(digit) * weights[index % len(weights)]
        for index, digit in enumerate(reversed(digits))
    )

    check_value = (11 - total % 11) % 11
    return "X" if check_value == 10 else str(check_value)


def generate_serial_number(
    connection: Connection,
    tenant_id: int,
    issue_year: int | None = None,
) -> str:
    year = issue_year if issue_year is not None else date.today().year

    if not 2000 <= year <= 9999:
        raise ValueError("Godina mora biti između 2000 i 9999.")

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT code
            FROM public.tenant
            WHERE id = %s
            """,
            (tenant_id,),
        )
        tenant = cursor.fetchone()

        if tenant is None:
            raise ValueError("Tenant ne postoji.")

        tenant_code = tenant[0]
        if tenant_code is None:
            raise ValueError("Tenant nema dodeljenu šifru.")

        cursor.execute(
            """
            INSERT INTO public.pass_serial_counter
                (tenant_id, issue_year, last_value)
            VALUES (%s, %s, 1)
            ON CONFLICT (tenant_id, issue_year)
            DO UPDATE
            SET last_value = public.pass_serial_counter.last_value + 1
            WHERE public.pass_serial_counter.last_value < 999999
            RETURNING last_value
            """,
            (tenant_id, year),
        )
        result = cursor.fetchone()

        if result is None:
            raise ValueError("Dostignut je limit serijskih brojeva za ovu godinu.")

        sequence = result[0]

    check_digit = calculate_check_digit(year, sequence)
    return f"{tenant_code}-{year:04d}-{sequence:06d}-{check_digit}"
