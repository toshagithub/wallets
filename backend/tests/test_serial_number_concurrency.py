
from concurrent.futures import ThreadPoolExecutor

from app.db.connection import tenant_connection
from app.wallet.serial_number import generate_serial_number


def test_concurrent_serial_numbers_are_unique():
    tenant_id = 1
    number_of_workers = 10

    def generate_one(_: int) -> str:
        with tenant_connection(tenant_id) as connection:
            return generate_serial_number(connection, tenant_id)

    with ThreadPoolExecutor(max_workers=number_of_workers) as executor:
        serial_numbers = list(
            executor.map(generate_one, range(number_of_workers))
        )

    assert len(serial_numbers) == number_of_workers
    assert len(set(serial_numbers)) == number_of_workers
