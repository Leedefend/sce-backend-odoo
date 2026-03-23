#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from system_init_minimal_surface_probe import fetch_system_init_payload


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "system_init_latency_budget_guard.json"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _budget(name: str, default: int) -> int:
    try:
        return int(os.getenv(name) or default)
    except Exception:
        return default


def _check(label: str, result: dict[str, Any], *, max_wall_ms: int, max_internal_ms: int, max_bytes: int) -> tuple[list[str], dict[str, Any]]:
    errors: list[str] = []
    meta = result.get("meta") if isinstance(result.get("meta"), dict) else {}
    startup_profile = meta.get("startup_profile") if isinstance(meta.get("startup_profile"), dict) else {}
    timings_ms = startup_profile.get("timings_ms") if isinstance(startup_profile.get("timings_ms"), dict) else {}
    wall_elapsed_ms = int(result.get("wall_elapsed_ms") or 0)
    internal_total_ms = int(startup_profile.get("total_ms") or 0)
    payload_bytes = int(result.get("payload_bytes") or 0)
    response = result.get("response") if isinstance(result.get("response"), dict) else {}
    data = response.get("data") if isinstance(response.get("data"), dict) else {}
    if wall_elapsed_ms > max_wall_ms:
        errors.append(f"{label} wall_elapsed_ms={wall_elapsed_ms} exceeds budget={max_wall_ms}")
    if internal_total_ms > max_internal_ms:
        errors.append(f"{label} startup_profile.total_ms={internal_total_ms} exceeds budget={max_internal_ms}")
    if payload_bytes > max_bytes:
        errors.append(f"{label} payload_bytes={payload_bytes} exceeds budget={max_bytes}")
    if not timings_ms:
        errors.append(f"{label} startup_profile.timings_ms missing")
    return errors, {
        "wall_elapsed_ms": wall_elapsed_ms,
        "internal_total_ms": internal_total_ms,
        "payload_bytes": payload_bytes,
        "response_key_count": len(data.keys()),
        "startup_profile": startup_profile,
    }


def main() -> int:
    errors: list[str] = []
    boot = fetch_system_init_payload(with_preload=False)
    preload = fetch_system_init_payload(with_preload=True)
    boot_errors, boot_report = _check(
        "boot",
        boot,
        max_wall_ms=_budget("SYSTEM_INIT_BOOT_MAX_WALL_MS", 5000),
        max_internal_ms=_budget("SYSTEM_INIT_BOOT_MAX_INTERNAL_MS", 4500),
        max_bytes=_budget("SYSTEM_INIT_BOOT_MAX_BYTES", 65536),
    )
    preload_errors, preload_report = _check(
        "preload",
        preload,
        max_wall_ms=_budget("SYSTEM_INIT_PRELOAD_MAX_WALL_MS", 7000),
        max_internal_ms=_budget("SYSTEM_INIT_PRELOAD_MAX_INTERNAL_MS", 6500),
        max_bytes=_budget("SYSTEM_INIT_PRELOAD_MAX_BYTES", 262144),
    )
    errors.extend(boot_errors)
    errors.extend(preload_errors)
    report = {
        "status": "PASS" if not errors else "FAIL",
        "boot": boot_report,
        "preload": preload_report,
        "errors": errors,
    }
    _write_json(OUT_JSON, report)
    if errors:
        print("[system_init_latency_budget_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[system_init_latency_budget_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
