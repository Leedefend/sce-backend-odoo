#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from pathlib import Path


EXPECTED = {
    "ENV": "dev",
    "ENV_FILE": ".env.dev",
    "DB_NAME": "sc_demo",
    "ACCEPTANCE_BASE_URL": "http://127.0.0.1:18081",
}


def _norm_env_file(value: str) -> str:
    if not value:
        return value
    path = Path(value)
    if path.is_absolute():
        try:
            return path.resolve().name if path.resolve().parent == Path.cwd().resolve() else path.as_posix()
        except OSError:
            return path.as_posix()
    return path.as_posix()


def main() -> int:
    errors: list[str] = []
    observed = {
        "ENV": os.getenv("ENV", "").strip(),
        "ENV_FILE": _norm_env_file(os.getenv("ENV_FILE", "").strip()),
        "DB_NAME": os.getenv("DB_NAME", "").strip(),
        "ACCEPTANCE_BASE_URL": os.getenv("ACCEPTANCE_BASE_URL", "").strip().rstrip("/"),
    }

    for key, expected in EXPECTED.items():
        if observed[key] != expected:
            errors.append(f"{key} must be {expected!r}, got {observed[key]!r}")

    if errors:
        print("[daily_dev_acceptance_env_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 2

    print("[daily_dev_acceptance_env_guard] PASS env=dev env_file=.env.dev db=sc_demo base_url=http://127.0.0.1:18081")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
