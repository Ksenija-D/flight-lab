"""Row validation: airport list loading, single-row checks, record building."""
from __future__ import annotations

import math
import re
from datetime import datetime

FIELD_COUNT = 6
FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
AIRPORT_RE = re.compile(r"[A-Z]{3}")
DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    codes = set()
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            code = line.strip()
            if code and not code.startswith("#"):
                codes.add(code)
    return codes


def is_valid_datetime(value: str) -> bool:
    """True if value is a real date and time written exactly as YYYY-MM-DD HH:MM."""
    if not isinstance(value, str) or not DATETIME_RE.fullmatch(value):
        return False
    try:
        datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        return False
    return True


def _is_airport(code: str, airports: set[str]) -> bool:
    return bool(AIRPORT_RE.fullmatch(code)) and code in airports


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    # 1. field count
    if len(fields) != FIELD_COUNT:
        return "WRONG_FIELD_COUNT"

    values = [f.strip() for f in fields]

    # 2. any field empty after stripping
    if any(v == "" for v in values):
        return "MISSING_FIELD"

    flight_id, origin, destination, departure, arrival, price_text = values

    # 3. flight id: 2-8 ASCII letters or digits
    if not FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

    # 4-5. airports: 3 uppercase ASCII letters and in the list
    if not _is_airport(origin, airports):
        return "INVALID_ORIGIN"
    if not _is_airport(destination, airports):
        return "INVALID_DESTINATION"

    # 6. origin equals destination
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    # 7-8. dates
    if not is_valid_datetime(departure):
        return "INVALID_DEPARTURE"
    if not is_valid_datetime(arrival):
        return "INVALID_ARRIVAL"

    # 9. arrival must be strictly after departure
    if datetime.strptime(arrival, DATETIME_FORMAT) <= datetime.strptime(departure, DATETIME_FORMAT):
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # 10. price must be a finite float
    try:
        price = float(price_text)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(price):
        return "INVALID_PRICE"

    # 11. price must be positive
    if price <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    values = [f.strip() for f in fields]
    return {
        "flight_id": values[0],
        "origin": values[1],
        "destination": values[2],
        "departure_datetime": values[3],
        "arrival_datetime": values[4],
        "price": float(values[5]),
    }
