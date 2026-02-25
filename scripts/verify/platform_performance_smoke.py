#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "scripts" / "verify" / "baselines" / "platform_performance_smoke.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "platform_performance_smoke.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "platform_performance_smoke.json"


def _safe_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
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


def _intent_call(intent_url: str, token: str, intent: str, params: dict) -> tuple[int, dict, float]:
    ts0 = time.perf_counter()
    status, payload = http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )
    elapsed_ms = (time.perf_counter() - ts0) * 1000.0
    return status, payload if isinstance(payload, dict) else {}, elapsed_ms


def main() -> int:
    baseline = _safe_json(BASELINE_JSON)
    iterations = int(baseline.get("iterations") or 8)
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
        errors.append("login failed for performance smoke")
        token = ""

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
    rows: list[dict] = []

    if token:
        for intent, params in targets:
            times: list[float] = []
            statuses: list[int] = []
            payload_sizes: list[int] = []
            for _ in range(iterations):
                status, payload, elapsed_ms = _intent_call(intent_url, token, intent, params)
                times.append(elapsed_ms)
                statuses.append(int(status))
                payload_sizes.append(len(json.dumps(payload, ensure_ascii=False).encode("utf-8")))
                if int(status) >= 500:
                    errors.append(f"{intent} returned 5xx status={status}")
            p95 = _p95(times)
            avg = (sum(times) / len(times)) if times else 0.0
            max_size = max(payload_sizes) if payload_sizes else 0
            threshold = float(max_p95.get(intent, 999999))
            size_threshold = int(max_payload.get(intent, 999999999))
            if p95 > threshold:
                errors.append(f"{intent} p95_ms exceeded: {p95:.2f} > {threshold:.2f}")
            if max_size > size_threshold:
                errors.append(f"{intent} payload_bytes exceeded: {max_size} > {size_threshold}")
            rows.append(
                {
                    "intent": intent,
                    "iterations": iterations,
                    "avg_ms": round(avg, 2),
                    "p95_ms": round(p95, 2),
                    "max_payload_bytes": max_size,
                    "status_codes": sorted(set(statuses)),
                    "threshold_p95_ms": threshold,
                    "threshold_payload_bytes": size_threshold,
                }
            )

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "target_count": len(rows),
            "iterations": iterations,
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
        "# Platform Performance Smoke",
        "",
        f"- target_count: {payload['summary']['target_count']}",
        f"- iterations: {iterations}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "| intent | avg_ms | p95_ms | max_payload_bytes | status_codes | p95_threshold | payload_threshold |",
        "|---|---:|---:|---:|---|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['intent']} | {row['avg_ms']:.2f} | {row['p95_ms']:.2f} | {row['max_payload_bytes']} | "
            f"{','.join(str(x) for x in row['status_codes'])} | {row['threshold_p95_ms']:.2f} | "
            f"{row['threshold_payload_bytes']} |"
        )
    lines.extend(["", "## Errors", ""])
    if errors:
        for item in errors:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(str(REPORT_MD))
    print(str(REPORT_JSON))
    if errors:
        print("[platform_performance_smoke] FAIL")
        return 2
    print("[platform_performance_smoke] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
