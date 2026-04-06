#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


ROOT = Path(__file__).resolve().parents[2]
NATIVE_DIR = ROOT / "addons/smart_core/app_config_engine/capability/native"
SERVICE = NATIVE_DIR / "native_projection_service.py"
SCHEMA = ROOT / "addons/smart_core/app_config_engine/capability/schema/capability_schema.py"

OUT_JSON = ROOT / "artifacts/backend/native_capability_projection_coverage_report.json"
OUT_MD = ROOT / "artifacts/backend/native_capability_projection_coverage_report.md"


TYPE_TO_ADAPTER = {
    "native_menu_entry": "menu_adapter.py",
    "native_window_action": "action_adapter.py",
    "native_model_access": "model_adapter.py",
    "native_server_action": "server_action_adapter.py",
    "native_report_action": "report_adapter.py",
    "native_view_binding": "view_binding_adapter.py",
}

TYPE_TO_CALL = {
    "native_menu_entry": "project_menu_capabilities",
    "native_window_action": "project_window_action_capabilities",
    "native_model_access": "project_model_access_capabilities",
    "native_server_action": "project_server_action_capabilities",
    "native_report_action": "project_report_action_capabilities",
    "native_view_binding": "project_view_binding_capabilities",
}


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _build_report() -> Dict[str, object]:
    service_text = _read(SERVICE)
    schema_text = _read(SCHEMA)

    rows: List[Dict[str, object]] = []
    for capability_type, adapter_file in TYPE_TO_ADAPTER.items():
        adapter_path = NATIVE_DIR / adapter_file
        adapter_text = _read(adapter_path)
        call_name = TYPE_TO_CALL.get(capability_type, "")
        rows.append(
            {
                "capability_type": capability_type,
                "adapter_file": str(adapter_path.relative_to(ROOT).as_posix()),
                "adapter_exists": adapter_path.is_file(),
                "schema_registered": capability_type in schema_text,
                "service_call_registered": call_name in service_text,
                "adapter_declares_type": capability_type in adapter_text,
            }
        )

    covered = [
        row
        for row in rows
        if bool(row.get("adapter_exists"))
        and bool(row.get("schema_registered"))
        and bool(row.get("service_call_registered"))
        and bool(row.get("adapter_declares_type"))
    ]

    payload: Dict[str, object] = {
        "ok": len(covered) == len(rows),
        "summary": {
            "total_types": len(rows),
            "covered_types": len(covered),
            "missing_types": len(rows) - len(covered),
        },
        "rows": rows,
    }
    return payload


def _write_outputs(payload: Dict[str, object]) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    lines = [
        "# Native Capability Projection Coverage Report",
        "",
        f"- total_types: {(payload.get('summary') or {}).get('total_types', 0)}",
        f"- covered_types: {(payload.get('summary') or {}).get('covered_types', 0)}",
        f"- missing_types: {(payload.get('summary') or {}).get('missing_types', 0)}",
        "",
        "| capability_type | adapter_exists | schema_registered | service_call_registered | adapter_declares_type |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {capability_type} | {adapter_exists} | {schema_registered} | {service_call_registered} | {adapter_declares_type} |".format(
                capability_type=row.get("capability_type", ""),
                adapter_exists=row.get("adapter_exists", False),
                schema_registered=row.get("schema_registered", False),
                service_call_registered=row.get("service_call_registered", False),
                adapter_declares_type=row.get("adapter_declares_type", False),
            )
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    payload = _build_report()
    _write_outputs(payload)
    print(str(OUT_JSON))
    print(str(OUT_MD))
    if not payload.get("ok"):
        print("[native_capability_projection_coverage_report] FAIL")
        return 2
    print("[native_capability_projection_coverage_report] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

