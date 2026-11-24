"""Running queries against the flight database."""
from __future__ import annotations

from validator import is_valid_datetime

RECORD_KEYS = ("flight_id", "origin", "destination",
               "departure_datetime", "arrival_datetime", "price")
STRING_KEYS = ("flight_id", "origin", "destination")
DATETIME_KEYS = ("departure_datetime", "arrival_datetime")
NUMBER_KEYS = ("price", "min_price")
ALLOWED_KEYS = set(RECORD_KEYS) | {"min_price", "sort_by", "order", "limit"}


def _is_number(value) -> bool:
    # Booleans are a subclass of int in Python but are not numbers here.
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_valid_query(query) -> bool:
    """True if the query object only uses allowed keys with values of the right type."""
    if not isinstance(query, dict):
        return False
    for key, value in query.items():
        if key not in ALLOWED_KEYS:
            return False
        if key in STRING_KEYS and not isinstance(value, str):
            return False
        if key in DATETIME_KEYS and not is_valid_datetime(value):
            return False
        if key in NUMBER_KEYS and not _is_number(value):
            return False
        if key == "sort_by" and not (isinstance(value, str) and value in RECORD_KEYS):
            return False
        if key == "order" and value not in ("asc", "desc"):
            return False
        if key == "limit" and not (isinstance(value, int) and not isinstance(value, bool) and value >= 0):
            return False
    if "order" in query and "sort_by" not in query:
        return False
    return True


def _matches(flight: dict, query: dict) -> bool:
    """True if the flight passes every filter condition in the query (AND)."""
    for key in STRING_KEYS:
        if key in query and flight.get(key) != query[key]:
            return False
    if "departure_datetime" in query and not flight["departure_datetime"] >= query["departure_datetime"]:
        return False
    if "arrival_datetime" in query and not flight["arrival_datetime"] <= query["arrival_datetime"]:
        return False
    if "price" in query and not flight["price"] <= query["price"]:
        return False
    if "min_price" in query and not flight["price"] >= query["min_price"]:
        return False
    return True


def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object.

    Valid query:   {"query": query, "matches": [...]}
    Invalid query: {"query": query, "error": "INVALID_QUERY", "matches": []}
    """
    if not is_valid_query(query):
        return {"query": query, "error": "INVALID_QUERY", "matches": []}

    matches = [flight for flight in db if _matches(flight, query)]
    if "sort_by" in query:
        key = query["sort_by"]
        # sorted() is stable, also with reverse=True, so ties keep database order.
        matches = sorted(matches, key=lambda f: f[key], reverse=query.get("order", "asc") == "desc")
    if "limit" in query:
        matches = matches[:query["limit"]]
    return {"query": query, "matches": [dict(f) for f in matches]}


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""
    if isinstance(queries, dict):
        queries = [queries]
    return [run_query(db, q) for q in queries]
