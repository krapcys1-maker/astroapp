from __future__ import annotations

from datetime import UTC, date, datetime, time
from zoneinfo import ZoneInfo

from app.models.birth_data import BirthData


def birth_data_to_utc_datetime(birth_data: BirthData) -> datetime:
    local_dt = datetime.combine(
        birth_data.birth_date,
        birth_data.birth_time,
        tzinfo=ZoneInfo(birth_data.timezone_name),
    )
    return local_dt.astimezone(UTC)


def local_datetime_to_utc(
    local_date: date,
    local_time: time,
    timezone_name: str,
) -> datetime:
    local_dt = datetime.combine(
        local_date,
        local_time,
        tzinfo=ZoneInfo(timezone_name),
    )
    return local_dt.astimezone(UTC)
