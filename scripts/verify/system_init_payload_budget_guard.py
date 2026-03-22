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
OUT_JSON = ROOT / "artifacts" / "backend" / "system_init_payload_budget_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "system_init_payload_budget_guard.md"


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    report: dict[str, Any] = {}
    try:
        max_bytes = int(os.getenv("SYSTEM_INIT_MAX_BYTES") or "65536")
        max_nav_count = int(os.getenv("SYSTEM_INIT_MAX_NAV_COUNT") or "80")
        max_intent_count = int(os.getenv("SYSTEM_INIT_MAX_INTENT_COUNT") or "300")

        result = fetch_system_init_payload()
        data = result.get("data") if isinstance(result.get("data"), dict) else {}
        nav = data.get("nav") if isinstance(data.get("nav"), list) else []
        intents = data.get("intents") if isinstance(data.get("intents"), list) else []
        payload_bytes = int(result.get("payload_bytes") or 0)

        if payload_bytes > max_bytes:
            errors.append(f"payload budget exceeded: {payload_bytes} > {max_bytes}")
        if len(nav) > max_nav_count:
            errors.append(f"nav count budget exceeded: {len(nav)} > {max_nav_count}")
        if len(intents) > max_intent_count:
            errors.append(f"intent count budget exceeded: {len(intents)} > {max_intent_count}")

        report = {
            "status": "PASS" if not errors else "FAIL",
            "budgets": {
                "max_bytes": max_bytes,
                "max_nav_count": max_nav_count,
                "max_intent_count": max_intent_count,
            },
            "actual": {
                "payload_bytes": payload_bytes,
                "nav_count": len(nav),
                "intent_count": len(intents),
            },
            "errors": errors,
        }
    except Exception as exc:
        report = {"status": "FAIL", "errors": [f"ENV_UNSTABLE: {exc}"]}
        errors = report["errors"]

    _write(OUT_JSON, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        "# System Init Payload Budget Guard",
        "",
        f"- status: {report.get('status', 'FAIL')}",
        f"- payload_bytes: {(report.get('actual') or {}).get('payload_bytes', '-')}",
        f"- nav_count: {(report.get('actual') or {}).get('nav_count', '-')}",
        f"- intent_count: {(report.get('actual') or {}).get('intent_count', '-')}",
        f"- max_bytes: {(report.get('budgets') or {}).get('max_bytes', '-')}",
        f"- max_nav_count: {(report.get('budgets') or {}).get('max_nav_count', '-')}",
        f"- max_intent_count: {(report.get('budgets') or {}).get('max_intent_count', '-')}",
    ]
    if errors:
        lines.extend(["", "## Errors", *[f"- {item}" for item in errors]])
    _write(OUT_MD, "\n".join(lines) + "\n")

    if errors:
        print("[system_init_payload_budget_guard] FAIL")
        for item in errors:
            print(f" - {item}")
        return 1
    print("[system_init_payload_budget_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

