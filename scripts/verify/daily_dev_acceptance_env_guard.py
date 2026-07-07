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
    "ACCEPTANCE_LOGIN": "wutao",
    "ACCEPTANCE_PROBE_OUTPUT": "artifacts/backend/dev_acceptance_release_probe.json",
    "FRONTEND_DIST_DIR": "./frontend/apps/web/dist-dev",
    "VITE_PLATFORM_ADMIN_DB": "sc_platform_core",
}

REQUIRED_NONEMPTY = (
    "ACCEPTANCE_PASSWORD",
)

FORBIDDEN_OVERRIDES = (
    "VITE_API_BASE_URL",
    "VITE_API_PROXY_TARGET",
    "VITE_ODOO_DB",
    "VITE_ODOO_DB_LOCKED",
    "VITE_APP_ENV",
    "VITE_BUILD_MODE",
    "VITE_BUILD_OUT_DIR",
    "VITE_DELIVERY_MODE",
    "VITE_FEATURE_FLAGS",
    "VITE_LITE_CONTRACT_PILOT",
    "VITE_LITE_CONTRACT_ROLLOUT",
    "VITE_TENANT",
)


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
        "ACCEPTANCE_LOGIN": os.getenv("ACCEPTANCE_LOGIN", "").strip(),
        "ACCEPTANCE_PROBE_OUTPUT": os.getenv("ACCEPTANCE_PROBE_OUTPUT", "").strip(),
        "FRONTEND_DIST_DIR": os.getenv("FRONTEND_DIST_DIR", "").strip(),
        "VITE_PLATFORM_ADMIN_DB": os.getenv("VITE_PLATFORM_ADMIN_DB", "").strip(),
    }

    for key, expected in EXPECTED.items():
        if observed[key] != expected:
            errors.append(f"{key} must be {expected!r}, got {observed[key]!r}")

    for key in REQUIRED_NONEMPTY:
        if not os.getenv(key, "").strip():
            errors.append(f"{key} must be set for daily acceptance release")

    for key in FORBIDDEN_OVERRIDES:
        value = os.getenv(key, "").strip()
        if value:
            errors.append(f"{key} must not be overridden for daily acceptance release, got {value!r}")

    if errors:
        print("[daily_dev_acceptance_env_guard] FAIL")
        for error in errors:
            print(f"- {error}")
        return 2

    print(
        "[daily_dev_acceptance_env_guard] PASS "
        "env=dev env_file=.env.dev db=sc_demo "
        "base_url=http://127.0.0.1:18081 "
        "login=wutao "
        "artifact=artifacts/backend/dev_acceptance_release_probe.json "
        "dist=./frontend/apps/web/dist-dev "
        "platform_admin_db=sc_platform_core"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
