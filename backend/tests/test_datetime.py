from datetime import datetime, timezone

import pytest

from app.utils.datetime import belgrade_to_utc, utc_to_belgrade


def test_winter_time_to_utc():
    result = belgrade_to_utc(datetime(2026, 11, 15, 0, 0))

    assert result == datetime(2026, 11, 14, 23, 0, tzinfo=timezone.utc)


def test_summer_time_to_utc():
    result = belgrade_to_utc(datetime(2026, 7, 15, 0, 0))

    assert result == datetime(2026, 7, 14, 22, 0, tzinfo=timezone.utc)


def test_utc_to_belgrade():
    result = utc_to_belgrade(
        datetime(2026, 11, 14, 23, 0, tzinfo=timezone.utc)
    )

    assert result.isoformat() == "2026-11-15T00:00:00+01:00"


def test_rejects_nonexistent_local_time():
    with pytest.raises(ValueError, match="ne postoji"):
        belgrade_to_utc(datetime(2026, 3, 29, 2, 30))


def test_rejects_ambiguous_local_time():
    with pytest.raises(ValueError, match="dvosmisleno"):
        belgrade_to_utc(datetime(2026, 10, 25, 2, 30))


def test_rejects_aware_input():
    with pytest.raises(ValueError, match="bez vremenske zone"):
        belgrade_to_utc(
            datetime(2026, 11, 15, 0, 0, tzinfo=timezone.utc)
        )
