#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
BASELINE_JSON = ROOT / "artifacts" / "backend" / "platform_sla_report.json"
REPORT_MD = ROOT / "docs" / "ops" / "audit" / "system_stability_stress_regression_report.md"
REPORT_JSON = ROOT / "artifacts" / "backend" / "system_stability_stress_regression_report.json"


def _load_json(path: Path) -> dict:
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


def _call(intent_url: str, token: str, intent: str, params: dict) -> tuple[int, dict, float]:
    ts0 = time.perf_counter()
    status, payload = http_post_json(
        intent_url,
        {"intent": intent, "params": params},
        headers={"Authorization": f"Bearer {token}"},
    )
    elapsed_ms = (time.perf_counter() - ts0) * 1000.0
    return status, payload if isinstance(payload, dict) else {}, elapsed_ms


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    base_url = get_base_url()
    intent_url = f"{base_url}/api/v1/intent"
    db_name = str(os.getenv("DB_NAME") or os.getenv("ODOO_DB") or "sc_dev").strip()
    login = str(os.getenv("E2E_LOGIN") or "admin").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "admin").strip()

    count_system_init = int(os.getenv("STRESS_COUNT_SYSTEM_INIT") or 200)
    count_ui_contract = int(os.getenv("STRESS_COUNT_UI_CONTRACT") or 200)
    count_execute_button = int(os.getenv("STRESS_COUNT_EXECUTE_BUTTON") or 1000)

    execute_model = str(os.getenv("STRESS_EXECUTE_MODEL") or "project.project").strip()
    execute_method = str(os.getenv("STRESS_EXECUTE_METHOD") or "action_sc_submit").strip()
    execute_res_id = int(os.getenv("STRESS_EXECUTE_RES_ID") or 4)

    baseline = _load_json(BASELINE_JSON)
    baseline_rows = baseline.get("rows") if isinstance(baseline.get("rows"), list) else []
    baseline_p95 = {
        str(row.get("intent") or "").strip(): float(row.get("p95_ms") or 0.0)
        for row in baseline_rows
        if isinstance(row, dict)
    }

    ok, token = _login(intent_url, db_name, login, password)
    if not ok:
        errors.append("login failed for stress regression")
        token = ""

    targets = [
        ("system.init", count_system_init, {"contract_mode": "user"}),
        ("ui.contract", count_ui_contract, {"op": "model", "model": "project.project", "view_type": "form"}),
        (
            "execute_button",
            count_execute_button,
            {
                "model": execute_model,
                "button": {"name": execute_method, "type": "object"},
                "res_id": execute_res_id,
                "dry_run": True,
            },
        ),
    ]

    rows: list[dict] = []
    if token:
        for intent, iterations, params in targets:
            times: list[float] = []
            statuses: list[int] = []
            payload_sizes: list[int] = []
            for _ in range(iterations):
                status, payload, elapsed = _call(intent_url, token, intent, params)
                times.append(elapsed)
                statuses.append(int(status))
                payload_sizes.append(len(json.dumps(payload, ensure_ascii=False).encode("utf-8")))
            p95 = _p95(times)
            avg = (sum(times) / len(times)) if times else 0.0
            non_2xx = len([x for x in statuses if x < 200 or x >= 300])
            error_rate = round(non_2xx / iterations, 6) if iterations else 0.0
            baseline_value = float(baseline_p95.get(intent, 0.0))

            if non_2xx > 0:
                errors.append(f"{intent} has non-2xx responses: {non_2xx}/{iterations}")
            if baseline_value > 0 and p95 > baseline_value:
                errors.append(f"{intent} p95 regression: {p95:.2f} > baseline {baseline_value:.2f}")
            if baseline_value == 0:
                warnings.append(f"{intent} baseline p95 missing, skip regression compare")

            rows.append(
                {
                    "intent": intent,
                    "iterations": iterations,
                    "avg_ms": round(avg, 2),
                    "p95_ms": round(p95, 2),
                    "baseline_p95_ms": round(baseline_value, 2),
                    "max_payload_bytes": max(payload_sizes) if payload_sizes else 0,
                    "non_2xx_count": non_2xx,
                    "error_rate": error_rate,
                    "statuses": sorted(set(statuses)),
                }
            )

    payload = {
        "ok": len(errors) == 0,
        "summary": {
            "target_count": len(rows),
            "total_calls": sum(int(row.get("iterations") or 0) for row in rows),
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "config": {
            "STRESS_COUNT_SYSTEM_INIT": count_system_init,
            "STRESS_COUNT_UI_CONTRACT": count_ui_contract,
            "STRESS_COUNT_EXECUTE_BUTTON": count_execute_button,
            "STRESS_EXECUTE_MODEL": execute_model,
            "STRESS_EXECUTE_METHOD": execute_method,
            "STRESS_EXECUTE_RES_ID": execute_res_id,
        },
        "rows": rows,
        "errors": errors,
        "warnings": warnings,
    }
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# System Stability Stress Regression Report",
        "",
        f"- total_calls: {payload['summary']['total_calls']}",
        f"- target_count: {payload['summary']['target_count']}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
        "| intent | iterations | avg_ms | p95_ms | baseline_p95_ms | non_2xx_count | error_rate | statuses |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['intent']} | {row['iterations']} | {row['avg_ms']:.2f} | {row['p95_ms']:.2f} | "
            f"{row['baseline_p95_ms']:.2f} | {row['non_2xx_count']} | {row['error_rate']:.6f} | "
            f"{','.join(str(x) for x in row['statuses'])} |"
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
        print("[system_stability_stress_regression] FAIL")
        return 2
    print("[system_stability_stress_regression] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

