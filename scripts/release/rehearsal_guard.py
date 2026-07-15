#!/usr/bin/env python3
"""Fail-closed guard for release rehearsal database operations."""
from __future__ import annotations

import os
import re
import sys


ALLOWED = re.compile(r"^sc_release_rehearsal(?:_(?:restored|rollback))?$")
FORBIDDEN = {
    "postgres",
    "sc_demo",
    "sc_frontend_acceptance",
    "sc_prod",
    "sc_prod_sim",
    os.environ.get("PROD_DB_NAME", ""),
    os.environ.get("PRODUCTION_DB_NAME", ""),
}


def validate(db_name: str | None = None) -> str:
    db = (db_name or os.environ.get("DB_NAME", "")).strip()
    if os.environ.get("SC_ENVIRONMENT") != "release_rehearsal":
        raise ValueError("SC_ENVIRONMENT must equal release_rehearsal")
    if os.environ.get("SC_ALLOW_DEMO_DATA", "0") not in {"", "0", "false", "False"}:
        raise ValueError("SC_ALLOW_DEMO_DATA must be disabled")
    if not db or db in FORBIDDEN or not ALLOWED.fullmatch(db):
        raise ValueError(f"database is not an allowed rehearsal name: {db or '<empty>'}")
    return db


if __name__ == "__main__":
    try:
        print(f"[release.guard] PASS db={validate()}")
    except ValueError as exc:
        print(f"[release.guard] FAIL {exc}", file=sys.stderr)
        raise SystemExit(2)
