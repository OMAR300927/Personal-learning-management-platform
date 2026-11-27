from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def validate_timezone(timezone_name: str) -> ZoneInfo:
    """Resolve a supported IANA timezone name."""
    try:
        return ZoneInfo(timezone_name)
    
    except ZoneInfoNotFoundError as error:
        raise ValueError("Unknown timezone") from error


def saturday_friday_week(
    occurred_at: datetime,
    timezone_name: str,
) -> tuple[datetime, datetime]:
    """Return the Saturday 00:00 and next Saturday 00:00 boundaries."""
    zone = validate_timezone(timezone_name)
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)

    local = occurred_at.astimezone(zone)
    local_midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    saturday = local_midnight - timedelta(days=(local.weekday() - 5) % 7)
    next_saturday = saturday + timedelta(days=7)
    return saturday, next_saturday


def current_saturday_friday_week(
    timezone_name: str,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Return the active Saturday-Friday boundaries for a timezone."""
    moment = now or datetime.now(timezone.utc)
    return saturday_friday_week(moment, timezone_name)


def is_ended_week(
    occurred_at: datetime,
    timezone_name: str,
    now: datetime | None = None,
) -> bool:
    """Return whether the entry's recalculated week has ended."""
    _, week_end = saturday_friday_week(occurred_at, timezone_name)
    moment = now or datetime.now(timezone.utc)
    zone = validate_timezone(timezone_name)
    local_now = moment.astimezone(zone)
    return local_now >= week_end
