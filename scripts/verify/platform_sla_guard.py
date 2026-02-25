#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "platform_sla.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "platform_sla_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "platform_sla_report.json"


def _load_baseline() -> dict:
    if not BASELINE_JSON.is_file():
        return {}
    try:
        payload = json.loads(BASELINE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    idx = int(round(0.95 * (len(arr) - 1)))
    return float(arr[idx])


def _login(intent_url: str, db_name: str, login: str, password: str) -> tuple[bool, str]:
    status, payload = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db_name, "login": login, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    if status >= 400 or not isinstance(payload, dict) or payload.get("ok") is not True:
        return False, ""
    data = payload.get("data") if isinstance(payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    return bool(token), token


def _call(intent_url: str, token: str, intent: str, params: dict) -> tuple[int, dict, float]:
    ts0 = time.perf_counter()
    status, payload = http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )
    elapsed_ms = (time.perf_counter() - ts0) * 1000.0
    return status, (payload if isinstance(payload, dict) else {}), elapsed_ms


def main() -> int:
    baseline = _load_baseline()
    iterations = int(baseline.get("iterations") or 6)
    max_p95 = baseline.get("max_p95_ms") if isinstance(baseline.get("max_p95_ms"), dict) else {}
    max_payload = baseline.get("max_payload_bytes") if isinstance(baseline.get("max_payload_bytes"), dict) else {}

    errors: list[str] = []
    warnings: list[str] = []
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed for platform SLA guard")
        token = ""

    rows: list[dict] = []
    targets = [
        ("system.init", {"contract_mode": "user"}),
        ("ui.contract", {"op": "model", "model": "project.project", "view_type": "form"}),
        (
            "execute_button",
            {
                "model": "project.project",
                "button": {"name": "action_view_tasks", "type": "object"},
                "res_id": 1,
                "dry_run": True,
            },
        ),
    ]

    if token:
        for intent, params in targets:
            times: list[float] = []
            sizes: list[int] = []
            statuses: list[int] = []
            for _ in range(iterations):
                status, payload, elapsed = _call(intent_url, token, intent, params)
                statuses.append(int(status))
                times.append(elapsed)
                sizes.append(len(json.dumps(payload, ensure_ascii=False).encode("utf-8")))
                if status >= 500:
                    errors.append(f"{intent} returns 5xx: {status}")
            p95 = _p95(times)
            max_size = max(sizes) if sizes else 0
            p95_limit = float(max_p95.get(intent, 999999.0))
            size_limit = int(max_payload.get(intent, 999999999))
            if p95 > p95_limit:
                errors.append(f"{intent} p95 exceeded SLA: {p95:.2f} > {p95_limit:.2f}")
            if max_size > size_limit:
                errors.append(f"{intent} payload exceeded SLA: {max_size} > {size_limit}")
            if any(400 <= s < 500 for s in statuses):
                warnings.append(f"{intent} has non-2xx statuses in SLA run: {sorted(set(statuses))}")
            rows.append(
                {
                    "intent": intent,
                    "iterations": iterations,
                    "p95_ms": round(p95, 2),
                    "max_payload_bytes": max_size,
                    "statuses": sorted(set(statuses)),
                    "p95_limit": p95_limit,
                    "payload_limit": size_limit,
                }
            )

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "iterations": iterations,
            "target_count": len(rows),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "rows": rows,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Platform SLA Report",
        "",
        f"- iterations: {iterations}",
        f"- target_count: {len(rows)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "| intent | p95_ms | p95_limit | max_payload_bytes | payload_limit | statuses |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['intent']} | {row['p95_ms']:.2f} | {row['p95_limit']:.2f} | "
            f"{row['max_payload_bytes']} | {row['payload_limit']} | "
            f"{','.join(str(s) for s in row['statuses'])} |"
        )
    lines.extend(["", "## Errors", ""])
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if warnings:
        for item in warnings:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[platform_sla_guard] FAIL")
        return 2
    print("[platform_sla_guard] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
