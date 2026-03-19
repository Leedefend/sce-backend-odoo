#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_JSON_PATH = ROOT / "artifacts" / "backend" / "scene_delivery_failure_brief.json"
REPORT_CANDIDATES = [
    "artifacts/backend/scene_product_delivery_readiness_report.json",
    "artifacts/backend/scene_base_contract_source_mix_role_matrix_report.json",
    "artifacts/backend/scene_base_contract_source_mix_company_matrix_report.json",
    "artifacts/backend/scene_base_contract_source_mix_report.json",
    "artifacts/backend/scene_company_snapshot_collect_report.json",
    "artifacts/backend/delivery_journey_role_matrix_report.json",
    "artifacts/backend/scene_company_access_preflight_report.json",
    "artifacts/backend/scene_multi_company_evidence_report.json",
    "artifacts/backend/scene_sample_registry_diff_report.json",
    "artifacts/backend/scene_governance_history_report.json",
]

MULTI_COMPANY_REPORTS = {
    "artifacts/backend/scene_company_snapshot_collect_report.json",
    "artifacts/backend/scene_company_access_preflight_report.json",
    "artifacts/backend/scene_multi_company_evidence_report.json",
    "artifacts/backend/scene_base_contract_source_mix_company_matrix_report.json",
}

PRECHECK_REPORTS = {
    "artifacts/backend/scene_company_snapshot_collect_report.json",
    "artifacts/backend/delivery_journey_role_matrix_report.json",
    "artifacts/backend/scene_company_access_preflight_report.json",
    "artifacts/backend/scene_multi_company_evidence_report.json",
}


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _load_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _report_status(path: Path) -> tuple[bool, list[str], dict]:
    payload = _load_json(path)
    if not payload:
        return False, ["missing_or_invalid_report"], {}
    ok = bool(payload.get("ok", False))
    errors = [str(item) for item in _as_list(payload.get("errors")) if str(item)]
    if not errors and not ok:
        summary = _as_dict(payload.get("summary"))
        errors = [f"summary={json.dumps(summary, ensure_ascii=False)}"] if summary else ["ok=false"]
    return ok, errors, payload


def _collect_multi_company_signals(rel: str, payload: dict) -> list[str]:
    signals: list[str] = []
    if rel not in MULTI_COMPANY_REPORTS:
        return signals
    warnings = [str(item) for item in _as_list(payload.get("warnings")) if str(item)]
    errors = [str(item) for item in _as_list(payload.get("errors")) if str(item)]
    summary = _as_dict(payload.get("summary"))
    if rel.endswith("scene_company_snapshot_collect_report.json"):
        observed = _as_list(summary.get("observed_company_ids"))
        signals.append(f"snapshot.observed_company_ids={observed}")
    if rel.endswith("scene_company_access_preflight_report.json"):
        reachable = summary.get("reachable_count")
        signals.append(f"preflight.reachable_count={reachable}")
    if rel.endswith("scene_multi_company_evidence_report.json"):
        observed = _as_dict(summary).get("current_observed_company_ids")
        historical = _as_dict(summary).get("historical_observed_company_ids")
        signals.append(f"evidence.current_observed_company_ids={observed}")
        signals.append(f"evidence.historical_observed_company_ids={historical}")
    for item in warnings:
        signals.append(f"warning={item}")
    for item in errors:
        signals.append(f"error={item}")
    return signals


def main() -> int:
    failed: list[dict[str, Any]] = []
    blocker_failed: list[dict[str, Any]] = []
    precheck_failed: list[dict[str, Any]] = []
    multi_company_signals: list[dict[str, Any]] = []
    multi_company_warnings: list[str] = []
    checked = 0
    for rel in REPORT_CANDIDATES:
        path = ROOT / rel
        if not path.exists():
            continue
        checked += 1
        ok, errors, payload = _report_status(path)
        signals = _collect_multi_company_signals(rel, payload)
        if signals:
            multi_company_signals.append({"path": rel, "signals": signals})
            for item in signals:
                if item.startswith("warning=") or item.startswith("error="):
                    multi_company_warnings.append(f"{rel}: {item}")
        if ok:
            continue
        row = {"path": rel, "errors": errors, "summary": _as_dict(payload.get("summary"))}
        failed.append(row)
        if rel in PRECHECK_REPORTS:
            precheck_failed.append(row)
        else:
            blocker_failed.append(row)

    print("[scene_delivery_failure_brief]")
    print(f"checked_reports={checked}")
    output = {
        "checked_reports": checked,
        "multi_company_highlight": bool(multi_company_signals),
        "multi_company_signals": multi_company_signals,
        "multi_company_warnings": multi_company_warnings,
        "failed_reports": [],
        "blocker_failures": [],
        "precheck_failures": [],
        "status": "",
        "multi_company_next_actions": [
            "make ops.scene.company_secondary.seed APPLY=1 CREATE_COMPANY_IF_MISSING=1 CREATE_USER_IF_MISSING=1",
            "make verify.scene.company_snapshot.collect",
            "SC_COMPANY_ACCESS_PREFLIGHT_STRICT=1 make verify.scene.company_access.preflight.guard",
            "SC_MULTI_COMPANY_EVIDENCE_STRICT=1 make verify.scene.delivery.readiness.role_company_matrix",
        ],
        "generated_by": "scripts/verify/scene_delivery_failure_brief.py",
    }
    if multi_company_signals:
        print("multi_company_highlight=1")
        for row in multi_company_signals:
            print(f"- multi_company_report={row['path']}")
            for item in row.get("signals") or []:
                print(f"  signal={item}")
    if multi_company_warnings:
        print(f"multi_company_warnings={len(multi_company_warnings)}")
        for item in multi_company_warnings:
            print(f"- multi_company_warning={item}")
        print("multi_company_next_actions=")
        print("- make ops.scene.company_secondary.seed APPLY=1 CREATE_COMPANY_IF_MISSING=1 CREATE_USER_IF_MISSING=1")
        print("- make verify.scene.company_snapshot.collect")
        print("- SC_COMPANY_ACCESS_PREFLIGHT_STRICT=1 make verify.scene.company_access.preflight.guard")
        print("- SC_MULTI_COMPANY_EVIDENCE_STRICT=1 make verify.scene.delivery.readiness.role_company_matrix")
    if not failed:
        print("failed_reports=0")
        print("status=NO_FAILURE_REPORT_DETECTED")
        output["status"] = "NO_FAILURE_REPORT_DETECTED"
        OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_JSON_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"output_json={OUTPUT_JSON_PATH.relative_to(ROOT).as_posix()}")
        return 0

    print(f"failed_reports={len(failed)}")
    print(f"blocker_failures={len(blocker_failed)}")
    print(f"precheck_failures={len(precheck_failed)}")
    output["failed_reports"] = failed
    output["blocker_failures"] = blocker_failed
    output["precheck_failures"] = precheck_failed
    output["status"] = "FAILURE_REPORT_DETECTED"
    if blocker_failed:
        print("[BLOCKER_FAILURES]")
    for row in blocker_failed:
        print(f"- report={row['path']}")
        for item in row.get("errors") or []:
            print(f"  error={item}")
        summary = _as_dict(row.get("summary"))
        if summary:
            print(f"  summary={json.dumps(summary, ensure_ascii=False)}")
    if precheck_failed:
        print("[PRECHECK_FAILURES]")
    for row in precheck_failed:
        print(f"- report={row['path']}")
        for item in row.get("errors") or []:
            print(f"  error={item}")
        summary = _as_dict(row.get("summary"))
        if summary:
            print(f"  summary={json.dumps(summary, ensure_ascii=False)}")
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"output_json={OUTPUT_JSON_PATH.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
