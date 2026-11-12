from datetime import datetime, timezone
from zoneinfo import ZoneInfo


BELGRADE_TZ = ZoneInfo("Europe/Belgrade")


def belgrade_to_utc(value: datetime) -> datetime:
    """Convert a Belgrade local datetime to an aware UTC datetime."""
    if value.tzinfo is not None:
        raise ValueError("Očekuje se lokalno vreme bez vremenske zone.")

    candidate = value.replace(tzinfo=BELGRADE_TZ, fold=0)

    roundtrip = candidate.astimezone(timezone.utc).astimezone(BELGRADE_TZ)

    if roundtrip.replace(tzinfo=None) != value:
        raise ValueError("Uneto lokalno vreme ne postoji zbog promene sata.")

    alternative = value.replace(
        tzinfo=BELGRADE_TZ,
        fold=1,
    ).astimezone(timezone.utc).astimezone(BELGRADE_TZ)

    if alternative.replace(tzinfo=None) == value:
        first_offset = candidate.utcoffset()
        second_offset = value.replace(
            tzinfo=BELGRADE_TZ,
            fold=1,
        ).utcoffset()

        if first_offset != second_offset:
            raise ValueError("Uneto lokalno vreme je dvosmisleno zbog promene sata.")

    return candidate.astimezone(timezone.utc)


def utc_to_belgrade(value: datetime) -> datetime:
    """Convert an aware datetime to Belgrade local time."""
    if value.tzinfo is None:
        raise ValueError("Očekuje se datetime sa vremenskom zonom.")

    return value.astimezone(BELGRADE_TZ)
