"""Reading CSV files into flight records and error messages."""
from __future__ import annotations

import csv
import os

from validator import to_record, validate_row


def _read_lines(path: str) -> list[str]:
    """Read a UTF-8 file and split it into lines, handling both \\n and \\r\\n."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        text = f.read()
    lines = text.split("\n")
    return [line[:-1] if line.endswith("\r") else line for line in lines]


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
      records - valid flight records, in input order
      errors  - one message per invalid row, in input order, formatted as
                "<file name>:<line number>: <ERROR_CODE> | <free text>"
                (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """
    records: list[dict] = []
    errors: list[str] = []
    seen: set[tuple[str, str]] = set()  # (flight_id, departure_datetime) of valid rows

    for path in paths:
        name = os.path.basename(path)
        lines = _read_lines(path)
        for line_number, line in enumerate(lines, start=1):
            if line_number == 1:
                continue  # header, never validated
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue  # blank line or comment

            try:
                fields = next(csv.reader([line]), [])
            except csv.Error:
                fields = []  # unparseable line: reported as WRONG_FIELD_COUNT
            code = validate_row(fields, airports)
            if code is None:
                record = to_record(fields)
                key = (record["flight_id"], record["departure_datetime"])
                if key in seen:
                    code = "DUPLICATE_FLIGHT"
                else:
                    seen.add(key)
                    records.append(record)

            if code is not None:
                errors.append(f"{name}:{line_number}: {code} | {line}")

    return records, errors
