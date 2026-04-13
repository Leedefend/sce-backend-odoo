#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts" / "v2" / "v2_primary_minimum_business_smoke_v1.json"


def _dispatch(intent: str, payload: Dict[str, Any], trace_id: str) -> Tuple[Dict[str, Any], float]:
    import sys

    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from v2.dispatcher import dispatch_intent  # type: ignore

    context = {"trace_id": trace_id, "user_id": 1, "company_id": 1}
    start = time.perf_counter()
    result = dispatch_intent(intent=intent, payload=payload, context=context)
    latency_ms = (time.perf_counter() - start) * 1000
    return result if isinstance(result, dict) else {}, latency_ms


def _has_contract_minimum(data: Dict[str, Any], expected_view_type: str) -> bool:
    required = {"intent", "model", "view_type", "status", "schema_validated"}
    actual_view_type = str(data.get("view_type") or "").strip().lower()
    expected = expected_view_type.strip().lower()
    view_type_ok = actual_view_type == expected
    if expected == "list" and actual_view_type in {"tree", "list"}:
        view_type_ok = True
    return required.issubset(set(data.keys())) and view_type_ok


def run_audit() -> Dict[str, Any]:
    errors: List[str] = []
    trace_ids: List[str] = []
    latency_summary: Dict[str, int] = {}

    bootstrap_result, bootstrap_latency = _dispatch("session.bootstrap", {"app_key": "platform"}, "iter1680-bootstrap")
    bootstrap_ok = bool(bootstrap_result.get("ok"))
    bootstrap_data = bootstrap_result.get("data") if isinstance(bootstrap_result.get("data"), dict) else {}
    bootstrap_meta = bootstrap_result.get("meta") if isinstance(bootstrap_result.get("meta"), dict) else {}
    trace_ids.append(str(bootstrap_meta.get("trace_id") or "iter1680-bootstrap"))
    latency_summary["session.bootstrap"] = int(bootstrap_meta.get("latency_ms") or round(bootstrap_latency))

    menu_navigation_ok = bool(bootstrap_data.get("bootstrap_ready")) and str(bootstrap_data.get("session_status") or "") == "ready"
    if not bootstrap_ok:
        errors.append("session.bootstrap_error")
    if not menu_navigation_ok:
        errors.append("menu_navigation_not_ready")

    meta_result, meta_latency = _dispatch("meta.describe_model", {"model": "project.project"}, "iter1680-meta")
    meta_ok = bool(meta_result.get("ok"))
    meta_data = meta_result.get("data") if isinstance(meta_result.get("data"), dict) else {}
    meta_meta = meta_result.get("meta") if isinstance(meta_result.get("meta"), dict) else {}
    trace_ids.append(str(meta_meta.get("trace_id") or "iter1680-meta"))
    latency_summary["meta.describe_model"] = int(meta_meta.get("latency_ms") or round(meta_latency))
    if not meta_ok:
        errors.append("meta.describe_model_error")
    if not isinstance(meta_data.get("fields"), dict) or not meta_data.get("fields"):
        errors.append("meta.describe_model_missing_fields")

    list_result, list_latency = _dispatch(
        "ui.contract",
        {"model": "project.project", "view_type": "list"},
        "iter1680-ui-list",
    )
    list_ok = bool(list_result.get("ok"))
    list_data = list_result.get("data") if isinstance(list_result.get("data"), dict) else {}
    list_meta = list_result.get("meta") if isinstance(list_result.get("meta"), dict) else {}
    trace_ids.append(str(list_meta.get("trace_id") or "iter1680-ui-list"))
    latency_summary["ui.contract.list"] = int(list_meta.get("latency_ms") or round(list_latency))
    if not list_ok:
        errors.append("ui.contract_list_error")
    if not _has_contract_minimum(list_data, "list"):
        errors.append("ui.contract_list_missing_required_fields")

    form_result, form_latency = _dispatch(
        "ui.contract",
        {"model": "project.project", "view_type": "form"},
        "iter1680-ui-form",
    )
    form_ok = bool(form_result.get("ok"))
    form_data = form_result.get("data") if isinstance(form_result.get("data"), dict) else {}
    form_meta = form_result.get("meta") if isinstance(form_result.get("meta"), dict) else {}
    trace_ids.append(str(form_meta.get("trace_id") or "iter1680-ui-form"))
    latency_summary["ui.contract.form"] = int(form_meta.get("latency_ms") or round(form_latency))
    if not form_ok:
        errors.append("ui.contract_form_error")
    if not _has_contract_minimum(form_data, "form"):
        errors.append("ui.contract_form_missing_required_fields")

    report = {
        "bootstrap": "PASS" if bootstrap_ok else "FAIL",
        "menu_navigation": "PASS" if menu_navigation_ok else "FAIL",
        "meta_describe_model": "PASS" if meta_ok and "meta.describe_model_missing_fields" not in errors else "FAIL",
        "ui_contract_list": "PASS" if list_ok and "ui.contract_list_missing_required_fields" not in errors else "FAIL",
        "ui_contract_form": "PASS" if form_ok and "ui.contract_form_missing_required_fields" not in errors else "FAIL",
        "trace_ids": trace_ids,
        "latency_summary": latency_summary,
        "errors": errors,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "gate_version": "v1",
        "gate_profile": "full",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "report": report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_audit()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"status={result['status']}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
