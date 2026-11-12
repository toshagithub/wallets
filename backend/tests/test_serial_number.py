from unittest.mock import MagicMock

import pytest

from app.wallet.serial_number import (
    calculate_check_digit,
    generate_serial_number,
)


@pytest.mark.parametrize(
    ("year", "sequence"),
    [
        (2026, 1),
        (2026, 42),
        (2026, 999999),
        (2000, 1),
        (9999, 999999),
    ],
)
def test_check_digit_is_valid_digit_or_x(year, sequence):
    assert calculate_check_digit(year, sequence) in "0123456789X"


@pytest.mark.parametrize(
    ("year", "sequence"),
    [
        (1999, 1),
        (10000, 1),
        (2026, 0),
        (2026, 1000000),
    ],
)
def test_check_digit_rejects_invalid_values(year, sequence):
    with pytest.raises(ValueError):
        calculate_check_digit(year, sequence)


def make_connection(fetchone_results):
    connection = MagicMock()
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.side_effect = fetchone_results
    return connection, cursor


def test_generate_serial_number_uses_tenant_code_and_counter():
    connection, cursor = make_connection([("AB",), (1,)])

    serial = generate_serial_number(connection, tenant_id=7, issue_year=2026)

    assert serial == f"AB-2026-000001-{calculate_check_digit(2026, 1)}"
    assert cursor.execute.call_count == 2


def test_generate_serial_number_rejects_unknown_tenant():
    connection, _ = make_connection([None])

    with pytest.raises(ValueError, match="Tenant ne postoji"):
        generate_serial_number(connection, tenant_id=999, issue_year=2026)


def test_generate_serial_number_rejects_tenant_without_code():
    connection, _ = make_connection([(None,)])

    with pytest.raises(ValueError, match="nema dodeljenu šifru"):
        generate_serial_number(connection, tenant_id=7, issue_year=2026)


def test_generate_serial_number_rejects_exhausted_counter():
    connection, _ = make_connection([("AB",), None])

    with pytest.raises(ValueError, match="Dostignut je limit"):
        generate_serial_number(connection, tenant_id=7, issue_year=2026)
