from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.models.birth_data import BirthData


def birth_data_to_utc_datetime(birth_data: BirthData) -> datetime:
    local_dt = datetime.combine(
        birth_data.birth_date,
        birth_data.birth_time,
        tzinfo=ZoneInfo(birth_data.timezone_name),
    )
    return local_dt.astimezone(UTC)
