"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

STUDENT_ID = "251RDC083"
FIRST_NAME = "Ksenija"
LAST_NAME = "Demchenko"

DEFAULT_OUTPUT = "db.json"
LOG_NAME = "errors.log"


class RuntimeProblem(Exception):
    """A problem with input files or folders: exit code 1."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight schedule CSV files, store valid flights as JSON and run queries.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database instead of parsing CSVs")
    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help=f"output path for the JSON database (default: {DEFAULT_OUTPUT})")
    parser.add_argument("-q", metavar="FILE", help="run the queries in this JSON file")
    parser.add_argument("-r", metavar="FOLDER", default=".", help="folder for the query response file (default: .)")
    return parser


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    """Parse and check the arguments. Raises SystemExit on usage errors (code 2) or -h (code 0)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if (args.i is not None or args.d is not None) and args.a is None:
        parser.error("-a is required with -i or -d")
    if args.j is not None and args.o is not None:
        parser.error("-o can only be used with -i or -d")
    return args


def csv_files_in_folder(folder: str) -> list[str]:
    """All files in folder (not sub-folders) whose name ends in .csv, in sorted filename order."""
    if not os.path.isdir(folder):
        raise RuntimeProblem(f"folder not found: {folder}")
    try:
        names = os.listdir(folder)
    except OSError as e:
        raise RuntimeProblem(f"cannot read folder {folder}: {e.strerror or e}") from e
    paths = [os.path.join(folder, n) for n in sorted(names)
             if n.endswith(".csv") and os.path.isfile(os.path.join(folder, n))]
    if not paths:
        raise RuntimeProblem(f"no .csv files found in folder: {folder}")
    return paths


def read_json_file(path: str, what: str):
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise RuntimeProblem(f"{what} not found: {path}") from e
    except OSError as e:
        raise RuntimeProblem(f"cannot read {what} {path}: {e.strerror or e}") from e
    except ValueError as e:  # JSONDecodeError and UnicodeDecodeError
        raise RuntimeProblem(f"{what} is not valid JSON: {path}") from e


def load_database(path: str) -> list[dict]:
    db = read_json_file(path, "JSON database")
    if not isinstance(db, list) or not all(isinstance(r, dict) for r in db):
        raise RuntimeProblem(f"JSON database must be an array of objects: {path}")
    return db


def load_queries(path: str):
    queries = read_json_file(path, "query file")
    if isinstance(queries, dict):
        return queries
    if isinstance(queries, list) and all(isinstance(q, dict) for q in queries):
        return queries
    raise RuntimeProblem(f"query file must contain a query object or an array of query objects: {path}")


def write_json(path: str, data, what: str) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
    except OSError as e:
        raise RuntimeProblem(f"cannot write {what} {path}: {e.strerror or e}") from e


def response_file_name() -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"


def parse_csv_sources(args: argparse.Namespace, logger: logging.Logger) -> list[dict]:
    """Read the airport list and the CSV file(s), log invalid rows and write the database."""
    try:
        airports = load_airports(args.a)
    except OSError as e:
        raise RuntimeProblem(f"cannot read airport file {args.a}: {e.strerror or e}") from e
    except UnicodeDecodeError as e:
        raise RuntimeProblem(f"airport file is not valid UTF-8: {args.a}") from e

    if args.i is not None:
        paths = [args.i]
    else:
        paths = csv_files_in_folder(args.d)

    for path in paths:
        if not os.path.isfile(path):
            raise RuntimeProblem(f"CSV file not found: {path}")

    try:
        records, errors = parse_files(paths, airports)
    except OSError as e:
        raise RuntimeProblem(f"cannot read CSV file: {e.filename or ''} {e.strerror or e}".strip()) from e
    except UnicodeDecodeError as e:
        raise RuntimeProblem("a CSV file is not valid UTF-8 text") from e

    for path in paths:
        logger.info("processing %s", os.path.basename(path))
    for message in errors:
        logger.warning(message)
    logger.info("%d valid rows, %d invalid rows", len(records), len(errors))

    write_json(args.o, records, "database")
    print(f"Wrote {len(records)} valid flights to {args.o} ({len(errors)} invalid rows logged).")
    return records


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """
    try:
        args = parse_args(argv)
    except SystemExit as e:  # argparse: usage error (2) or -h (0)
        return e.code if isinstance(e.code, int) else (0 if e.code is None else 2)

    logger = logging.getLogger("flight_parser")
    handler = None
    try:
        if args.j is None:
            if args.o is None:
                args.o = DEFAULT_OUTPUT
            log_path = os.path.join(os.path.dirname(os.path.abspath(args.o)), LOG_NAME)
            logger.setLevel(logging.INFO)
            try:
                handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
            except OSError as e:
                raise RuntimeProblem(f"cannot write log file {log_path}: {e.strerror or e}") from e
            handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
            logger.addHandler(handler)
            db = parse_csv_sources(args, logger)
        else:
            db = load_database(args.j)
            print(f"Loaded {len(db)} flights from {args.j}.")

        if args.q is not None:
            queries = load_queries(args.q)
            if not os.path.isdir(args.r):
                raise RuntimeProblem(f"response folder not found: {args.r}")
            response = run_queries(db, queries)
            out_path = os.path.join(args.r, response_file_name())
            write_json(out_path, response, "response file")
            print(f"Wrote {len(response)} query results to {out_path}.")
        return 0
    except RuntimeProblem as e:
        if handler is not None:
            logger.error(str(e))
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:  # last resort: never show a traceback
        if handler is not None:
            logger.error("unexpected error: %s", e)
        print(f"Error: unexpected problem: {e}", file=sys.stderr)
        return 1
    finally:
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
