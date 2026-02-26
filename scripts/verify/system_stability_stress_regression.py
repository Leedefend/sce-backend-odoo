#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import statistics
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


def _percentile(values: list[float], ratio: float) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    idx = int(round(ratio * (len(arr) - 1)))
    idx = max(0, min(idx, len(arr) - 1))
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


def _thresholds(intent: str, baseline_p95: float) -> tuple[float, float]:
    rel_warn = float(os.getenv("STRESS_WARN_REL_FACTOR") or 1.05)
    rel_fail = float(os.getenv("STRESS_FAIL_REL_FACTOR") or 1.10)
    abs_warn_defaults = {"system.init": 80.0, "ui.contract": 15.0, "execute_button": 5.0}
    abs_fail_defaults = {"system.init": 150.0, "ui.contract": 30.0, "execute_button": 10.0}
    abs_warn = float(os.getenv(f"STRESS_WARN_ABS_{intent.upper().replace('.', '_')}") or abs_warn_defaults.get(intent, 20.0))
    abs_fail = float(os.getenv(f"STRESS_FAIL_ABS_{intent.upper().replace('.', '_')}") or abs_fail_defaults.get(intent, 40.0))
    warn_th = max(baseline_p95 * rel_warn, baseline_p95 + abs_warn)
    fail_th = max(baseline_p95 * rel_fail, baseline_p95 + abs_fail)
    if intent == "execute_button":
        # Absolute threshold prevents tiny baselines from over-sensitive fail decisions.
        warn_th = max(warn_th, 60.0)
        fail_th = max(fail_th, 80.0)
    return warn_th, fail_th


def _grade_round(intent: str, p95_ms: float, baseline_p95: float) -> tuple[str, float, float]:
    if baseline_p95 <= 0:
        return "warn", 0.0, 0.0
    warn_th, fail_th = _thresholds(intent, baseline_p95)
    if p95_ms > fail_th:
        return "fail", warn_th, fail_th
    if p95_ms > warn_th:
        return "warn", warn_th, fail_th
    return "pass", warn_th, fail_th


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
    rounds = int(os.getenv("STRESS_ROUNDS") or 3)
    warmup_count = int(os.getenv("STRESS_WARMUP") or 20)
    fail_rounds_required = int(os.getenv("STRESS_FAIL_ROUNDS_REQUIRED") or 2)

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
            round_rows: list[dict] = []
            all_times: list[float] = []
            all_statuses: list[int] = []
            all_payload_sizes: list[int] = []
            baseline_value = float(baseline_p95.get(intent, 0.0))
            if baseline_value <= 0:
                warnings.append(f"{intent} baseline p95 missing, grade defaults to WARN")

            for round_index in range(1, rounds + 1):
                # Warmup phase: ignored in metrics.
                for _ in range(max(0, warmup_count)):
                    _call(intent_url, token, intent, params)

                times: list[float] = []
                statuses: list[int] = []
                payload_sizes: list[int] = []
                for _ in range(iterations):
                    status, payload, elapsed = _call(intent_url, token, intent, params)
                    times.append(elapsed)
                    statuses.append(int(status))
                    payload_sizes.append(len(json.dumps(payload, ensure_ascii=False).encode("utf-8")))

                p50 = _percentile(times, 0.50)
                p95 = _percentile(times, 0.95)
                p99 = _percentile(times, 0.99)
                avg = (sum(times) / len(times)) if times else 0.0
                var = statistics.pvariance(times) if len(times) > 1 else 0.0
                non_2xx = len([x for x in statuses if x < 200 or x >= 300])
                grade, warn_th, fail_th = _grade_round(intent, p95, baseline_value)
                round_rows.append(
                    {
                        "round": round_index,
                        "iterations": iterations,
                        "warmup": warmup_count,
                        "avg_ms": round(avg, 2),
                        "p50_ms": round(p50, 2),
                        "p95_ms": round(p95, 2),
                        "p99_ms": round(p99, 2),
                        "variance_ms2": round(var, 2),
                        "max_ms": round(max(times) if times else 0.0, 2),
                        "baseline_p95_ms": round(baseline_value, 2),
                        "warn_threshold_ms": round(warn_th, 2),
                        "fail_threshold_ms": round(fail_th, 2),
                        "grade": grade,
                        "non_2xx_count": non_2xx,
                        "statuses": sorted(set(statuses)),
                        "max_payload_bytes": max(payload_sizes) if payload_sizes else 0,
                    }
                )
                all_times.extend(times)
                all_statuses.extend(statuses)
                all_payload_sizes.extend(payload_sizes)

            round_fail_count = sum(1 for x in round_rows if x["grade"] == "fail")
            round_warn_count = sum(1 for x in round_rows if x["grade"] == "warn")
            non_2xx_total = len([x for x in all_statuses if x < 200 or x >= 300])
            error_rate = round(non_2xx_total / len(all_statuses), 6) if all_statuses else 0.0
            overall_p95 = _percentile(all_times, 0.95)
            overall_p50 = _percentile(all_times, 0.50)
            overall_p99 = _percentile(all_times, 0.99)
            overall_grade = "pass"
            if non_2xx_total > 0:
                overall_grade = "fail"
                errors.append(f"{intent} non-2xx detected: {non_2xx_total}/{len(all_statuses)}")
            elif round_fail_count >= fail_rounds_required:
                overall_grade = "fail"
                errors.append(
                    f"{intent} fail rounds {round_fail_count}/{rounds} (required>={fail_rounds_required})"
                )
            elif round_warn_count > 0:
                overall_grade = "warn"
                warnings.append(f"{intent} has warn rounds {round_warn_count}/{rounds}")

            rows.append(
                {
                    "intent": intent,
                    "rounds": rounds,
                    "iterations_per_round": iterations,
                    "warmup_per_round": warmup_count,
                    "baseline_p95_ms": round(baseline_value, 2),
                    "overall_grade": overall_grade,
                    "overall_p50_ms": round(overall_p50, 2),
                    "overall_p95_ms": round(overall_p95, 2),
                    "overall_p99_ms": round(overall_p99, 2),
                    "overall_max_ms": round(max(all_times) if all_times else 0.0, 2),
                    "max_payload_bytes": max(all_payload_sizes) if all_payload_sizes else 0,
                    "non_2xx_count": non_2xx_total,
                    "error_rate": error_rate,
                    "statuses": sorted(set(all_statuses)),
                    "round_fail_count": round_fail_count,
                    "round_warn_count": round_warn_count,
                    "rounds_detail": round_rows,
                }
            )

    overall_status = "pass"
    if errors:
        overall_status = "fail"
    elif warnings:
        overall_status = "warn"
    payload = {
        "ok": len(errors) == 0,
        "status": overall_status,
        "summary": {
            "target_count": len(rows),
            "total_calls": sum(int(row.get("iterations_per_round") or 0) * int(row.get("rounds") or 1) for row in rows),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "rounds": rounds,
            "warmup_per_round": warmup_count,
            "fail_rounds_required": fail_rounds_required,
        },
        "config": {
            "STRESS_COUNT_SYSTEM_INIT": count_system_init,
            "STRESS_COUNT_UI_CONTRACT": count_ui_contract,
            "STRESS_COUNT_EXECUTE_BUTTON": count_execute_button,
            "STRESS_ROUNDS": rounds,
            "STRESS_WARMUP": warmup_count,
            "STRESS_FAIL_ROUNDS_REQUIRED": fail_rounds_required,
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
        f"- status: {overall_status.upper()}",
        f"- total_calls: {payload['summary']['total_calls']}",
        f"- target_count: {payload['summary']['target_count']}",
        f"- rounds: {rounds}",
        f"- warmup_per_round: {warmup_count}",
        f"- fail_rounds_required: {fail_rounds_required}",
        f"- error_count: {payload['summary']['error_count']}",
        f"- warning_count: {payload['summary']['warning_count']}",
        "",
        "| intent | overall_grade | rounds | p50_ms | p95_ms | p99_ms | baseline_p95_ms | fail_rounds | warn_rounds | error_rate | statuses |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['intent']} | {row['overall_grade']} | {row['rounds']} | {row['overall_p50_ms']:.2f} | "
            f"{row['overall_p95_ms']:.2f} | {row['overall_p99_ms']:.2f} | {row['baseline_p95_ms']:.2f} | "
            f"{row['round_fail_count']} | {row['round_warn_count']} | {row['error_rate']:.6f} | "
            f"{','.join(str(x) for x in row['statuses'])} |"
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
        print("[system_stability_stress_regression] FAIL")
        return 2
    if warnings:
        print("[system_stability_stress_regression] PASS_WITH_WARNINGS")
        return 0
    print("[system_stability_stress_regression] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
