#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "artifacts" / "v2" / "v1_v2_focus_intent_diff_report_v1.json"
LEGACY_BASELINE = ROOT / "artifacts" / "contract" / "rootfix" / "menu_278_admin.json"


def _dispatch(intent: str, payload: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    sys.path.insert(0, str(ROOT / "addons" / "smart_core"))
    from v2.dispatcher import dispatch_intent  # type: ignore

    context = {"trace_id": trace_id, "user_id": 1, "company_id": 1}
    result = dispatch_intent(intent=intent, payload=payload, context=context)
    return result if isinstance(result, dict) else {}


def _legacy_fields_baseline() -> Dict[str, Any]:
    if not LEGACY_BASELINE.exists():
        return {}
    payload = json.loads(LEGACY_BASELINE.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    raw = payload.get("ui_contract_raw") if isinstance(payload.get("ui_contract_raw"), dict) else {}
    fields = raw.get("fields") if isinstance(raw.get("fields"), dict) else {}
    return fields


def _meta_diff(v1_fields: Dict[str, Any], v2_fields: Dict[str, Any]) -> Dict[str, Any]:
    v1_names = list(v1_fields.keys())
    v2_names = list(v2_fields.keys())
    shared = [name for name in v2_names if name in v1_fields]

    modifier_diff: List[Dict[str, Any]] = []
    for name in shared:
        v1_item = v1_fields.get(name) if isinstance(v1_fields.get(name), dict) else {}
        v2_item = v2_fields.get(name) if isinstance(v2_fields.get(name), dict) else {}
        item_diff = {}
        for key in ("readonly", "required", "invisible"):
            if key not in v1_item or key not in v2_item:
                continue
            if bool(v1_item.get(key)) != bool(v2_item.get(key)):
                item_diff[key] = {"v1": bool(v1_item.get(key)), "v2": bool(v2_item.get(key))}
        if item_diff:
            modifier_diff.append({"field": name, "diff": item_diff})

    return {
        "field_count_diff": len(v2_names) - len(v1_names),
        "field_order_changed": [name for name in shared] != [name for name in v1_names if name in v2_fields],
        "type_diff": [
            {
                "field": name,
                "v1": str((v1_fields.get(name) or {}).get("type") or ""),
                "v2": str((v2_fields.get(name) or {}).get("type") or ""),
            }
            for name in shared
            if str((v1_fields.get(name) or {}).get("type") or "") != str((v2_fields.get(name) or {}).get("type") or "")
        ],
        "modifier_diff": modifier_diff,
    }


def _ui_contract_diff(v1_contract: Dict[str, Any], list_data: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
    v1_layout_blocks = set()
    for key in ("headerButtons", "statButtons", "sheet", "chatter", "ribbon"):
        if key in v1_contract:
            v1_layout_blocks.add(key)

    v2_layout_blocks = set()
    for candidate in (list_data, form_data):
        for key in ("layout", "groups", "notebook", "pages", "header_buttons", "stat_buttons", "chatter"):
            if key in candidate:
                v2_layout_blocks.add(key)

    if not v2_layout_blocks:
        v2_layout_blocks = {"status", "view_type", "model"}

    missing = sorted(v1_layout_blocks - v2_layout_blocks)
    extra = sorted(v2_layout_blocks - v1_layout_blocks)
    layout_diff: List[str] = []
    if missing:
        layout_diff.append("missing_legacy_layout_blocks")
    if extra:
        layout_diff.append("extra_v2_layout_blocks")

    return {
        "layout_diff": layout_diff,
        "missing_blocks": missing,
        "extra_blocks": extra,
    }


def _session_diff(bootstrap_data: Dict[str, Any]) -> Dict[str, Any]:
    menu_diff: List[Dict[str, Any]] = []
    route_diff: List[Dict[str, Any]] = []
    registry_count = int(bootstrap_data.get("registry_count") or 0)
    if registry_count <= 0:
        menu_diff.append({"item": "registry_count", "issue": "non_positive"})
    session_status = str(bootstrap_data.get("session_status") or "")
    if session_status != "ready":
        route_diff.append({"item": "session_status", "expected": "ready", "actual": session_status})
    return {"menu_diff": menu_diff, "route_diff": route_diff}


def _risk_level(meta: Dict[str, Any], ui: Dict[str, Any], session: Dict[str, Any]) -> str:
    if session.get("route_diff") and any(item.get("item") == "session_status" for item in session.get("route_diff", [])):
        return "P0"
    if meta.get("modifier_diff"):
        return "P1"
    if ui.get("missing_blocks"):
        return "P2"
    if meta.get("field_order_changed") or meta.get("type_diff") or ui.get("extra_blocks") or session.get("menu_diff"):
        return "P3"
    return "LOW"


def run_audit() -> Dict[str, Any]:
    errors: List[str] = []

    bootstrap = _dispatch("session.bootstrap", {"app_key": "platform"}, "iter1680-diff-bootstrap")
    meta = _dispatch("meta.describe_model", {"model": "project.project"}, "iter1680-diff-meta")
    ui_list = _dispatch("ui.contract", {"model": "project.project", "view_type": "list"}, "iter1680-diff-list")
    ui_form = _dispatch("ui.contract", {"model": "project.project", "view_type": "form"}, "iter1680-diff-form")

    if not all(bool(item.get("ok")) for item in (bootstrap, meta, ui_list, ui_form)):
        errors.append("focus_intent_runtime_error")

    v2_fields = (meta.get("data") or {}).get("fields") if isinstance((meta.get("data") or {}).get("fields"), dict) else {}
    v1_fields = _legacy_fields_baseline() or v2_fields

    v1_contract = {}
    if LEGACY_BASELINE.exists():
        payload = json.loads(LEGACY_BASELINE.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and isinstance(payload.get("ui_contract"), dict):
            v1_contract = payload.get("ui_contract") or {}

    meta_diff = _meta_diff(v1_fields=v1_fields, v2_fields=v2_fields)
    ui_diff = _ui_contract_diff(
        v1_contract=v1_contract,
        list_data=ui_list.get("data") if isinstance(ui_list.get("data"), dict) else {},
        form_data=ui_form.get("data") if isinstance(ui_form.get("data"), dict) else {},
    )
    session_diff = _session_diff(bootstrap_data=bootstrap.get("data") if isinstance(bootstrap.get("data"), dict) else {})
    risk_level = _risk_level(meta_diff, ui_diff, session_diff)

    report = {
        "meta.describe_model": {
            "field_count_diff": meta_diff.get("field_count_diff", 0),
            "field_order_changed": bool(meta_diff.get("field_order_changed")),
            "modifier_diff": meta_diff.get("modifier_diff", []),
            "type_diff": meta_diff.get("type_diff", []),
        },
        "ui.contract": {
            "layout_diff": ui_diff.get("layout_diff", []),
            "missing_blocks": ui_diff.get("missing_blocks", []),
            "extra_blocks": ui_diff.get("extra_blocks", []),
        },
        "session.bootstrap": {
            "menu_diff": session_diff.get("menu_diff", []),
            "route_diff": session_diff.get("route_diff", []),
        },
        "risk_level": risk_level,
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if risk_level in {"P0", "P1"}:
        errors.append(f"high_risk_diff:{risk_level}")

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
