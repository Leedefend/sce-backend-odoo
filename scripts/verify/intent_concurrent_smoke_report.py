#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import concurrent.futures
import json
import os
import threading
import time
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "intent_concurrent_smoke_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "intent_concurrent_smoke_report.json"


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


def _call_intent(intent_url: str, token: str, intent: str, params: dict) -> dict:
    ts0 = time.perf_counter()
    status, payload = http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )
    elapsed_ms = (time.perf_counter() - ts0) * 1000.0
    ok = isinstance(payload, dict) and payload.get("ok") is True
    keys = sorted(list(payload.keys())) if isinstance(payload, dict) else []
    return {
        "intent": intent,
        "status": int(status),
        "ok": bool(ok),
        "elapsed_ms": round(elapsed_ms, 2),
        "keys": keys,
    }


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()
    workers = int(os.getenv("CONCURRENT_WORKERS") or 12)
    rounds = int(os.getenv("CONCURRENT_ROUNDS") or 4)

    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed for concurrent smoke")
        token = ""

    matrix = [
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

    results: list[dict] = []
    lock = threading.Lock()
    if token:
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
            futures = []
            for _ in range(rounds):
                for intent, params in matrix:
                    futures.append(pool.submit(_call_intent, intent_url, token, intent, params))
            for fut in concurrent.futures.as_completed(futures):
                row = fut.result()
                with lock:
                    results.append(row)

    per_intent = {}
    for intent, _ in matrix:
        subset = [r for r in results if r.get("intent") == intent]
        statuses = sorted(set(int(r.get("status") or 0) for r in subset))
        key_sets = sorted(set(",".join(r.get("keys") or []) for r in subset))
        p95 = 0.0
        if subset:
            times = sorted(float(r.get("elapsed_ms") or 0.0) for r in subset)
            idx = int(round(0.95 * (len(times) - 1)))
            p95 = float(times[idx])
        per_intent[intent] = {
            "count": len(subset),
            "statuses": statuses,
            "shape_variants": len(key_sets),
            "p95_ms": round(p95, 2),
        }
        if any(s >= 500 for s in statuses):
            errors.append(f"{intent} has 5xx under concurrency")
        if len(key_sets) > 2:
            errors.append(f"{intent} response shape unstable under concurrency")
        if subset and any(not bool(r.get("ok")) and int(r.get("status") or 0) < 500 for r in subset):
            warnings.append(f"{intent} has non-ok responses (non-5xx)")

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "workers": workers,
            "rounds": rounds,
            "request_count": len(results),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "per_intent": per_intent,
        "errors": errors,
        "warnings": warnings,
    }

    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Intent Concurrent Smoke Report",
        "",
        f"- workers: {workers}",
        f"- rounds: {rounds}",
        f"- request_count: {len(results)}",
        f"- error_count: {len(errors)}",
        f"- warning_count: {len(warnings)}",
        "",
        "| intent | count | statuses | shape_variants | p95_ms |",
        "|---|---:|---|---:|---:|",
    ]
    for intent, row in per_intent.items():
        lines.append(
            f"| {intent} | {row['count']} | {','.join(str(s) for s in row['statuses'])} | "
            f"{row['shape_variants']} | {row['p95_ms']:.2f} |"
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
        print("[intent_concurrent_smoke_report] FAIL")
        return 2
    print("[intent_concurrent_smoke_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
