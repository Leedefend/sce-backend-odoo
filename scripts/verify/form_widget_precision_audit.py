#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_widget_precision_v1.json"
CONTAINER_KEYS = ("children", "tabs", "pages", "nodes", "items")
FOCUS_FIELDS = {
    "description",
    "active",
    "allow_rating",
    "alias_contact",
    "privacy_visibility",
    "lifecycle_state",
    "task_ids",
    "collaborator_ids",
}
GENERIC_WIDGETS = {"", "char", "text", "input", "textarea"}
RELATIONAL_TYPES = {"many2one", "one2many", "many2many"}
CONTRACT_SERVICE_PATH = ROOT / "addons" / "smart_core" / "app_config_engine" / "services" / "contract_service.py"


def _load_payload(path: Path) -> dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(loaded, dict):
        return loaded
    return {}


def _walk_layout(node: Any):
    if isinstance(node, dict):
        yield node
        for key in CONTAINER_KEYS:
            value = node.get(key)
            if isinstance(value, list):
                for child in value:
                    yield from _walk_layout(child)
        return
    if isinstance(node, list):
        for item in node:
            yield from _walk_layout(item)


def _field_type(descriptor: dict[str, Any]) -> str:
    return str(descriptor.get("type") or descriptor.get("ttype") or "").strip().lower()


def _canonical_widget(field_type: str) -> str:
    mapping = {
        "many2one": "many2one",
        "one2many": "one2many_list",
        "many2many": "many2many_tags",
        "boolean": "boolean",
        "html": "html",
        "selection": "selection",
    }
    return mapping.get(field_type, field_type)


def _build_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    form = ((data.get("views") if isinstance(data.get("views"), dict) else {}).get("form") if isinstance((data.get("views") if isinstance(data.get("views"), dict) else {}).get("form"), dict) else {})
    layout = form.get("layout")

    rows: list[dict[str, Any]] = []
    for node in _walk_layout(layout):
        if str(node.get("type") or "").strip().lower() != "field":
            continue
        field_name = str(node.get("name") or "").strip()
        if not field_name:
            continue
        descriptor = fields.get(field_name) if isinstance(fields.get(field_name), dict) else {}
        if not descriptor:
            continue

        field_type = _field_type(descriptor)
        field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}
        widget = str(field_info.get("widget") or "").strip().lower()
        canonical = _canonical_widget(field_type)

        issues: list[str] = []
        blocking = False

        if field_type in {"html", "boolean", "selection"} and widget in GENERIC_WIDGETS:
            issues.append("GENERIC_WIDGET_FOR_TYPED_FIELD")
            blocking = True

        if field_type in RELATIONAL_TYPES and widget in GENERIC_WIDGETS:
            issues.append("RELATIONAL_WIDGET_DEGRADED")
            blocking = True

        if field_type == "selection" and field_name == "lifecycle_state" and widget not in {"statusbar", "selection", "radio"}:
            issues.append("LIFECYCLE_SELECTION_WIDGET_UNEXPECTED")
            blocking = True

        if issues or field_name in FOCUS_FIELDS:
            rows.append({
                "field": field_name,
                "focus": field_name in FOCUS_FIELDS,
                "type": field_type,
                "widget": widget,
                "canonical_widget": canonical,
                "issues": issues,
                "blocking": blocking,
            })
    return rows


def run_audit(input_path: Path) -> dict[str, Any]:
    payload = _load_payload(input_path)
    rows = _build_rows(payload)
    blocking_rows = [row for row in rows if row.get("blocking")]

    contract_service_text = CONTRACT_SERVICE_PATH.read_text(encoding="utf-8") if CONTRACT_SERVICE_PATH.exists() else ""
    code_guard = {
        "has_html_widget_fix": "canonical_type == \"html\"" in contract_service_text,
        "has_boolean_widget_fix": "canonical_type == \"boolean\"" in contract_service_text,
        "has_selection_widget_fix": "canonical_type == \"selection\"" in contract_service_text,
    }
    code_guard_pass = all(bool(v) for v in code_guard.values())
    snapshot_outdated = code_guard_pass and len(blocking_rows) > 0
    status = "PASS" if code_guard_pass and (len(blocking_rows) == 0 or snapshot_outdated) else "BLOCKED"

    result = {
        "version": "v1",
        "audit": "form_widget_precision",
        "target": {
            "input": str(input_path),
        },
        "summary": {
            "status": status,
            "issue_count": len(rows),
            "blocking_count": len(blocking_rows),
            "focus_issue_count": len([row for row in rows if row.get("focus") and row.get("issues")]),
            "snapshot_outdated": snapshot_outdated,
            "code_guard_pass": code_guard_pass,
        },
        "code_guard": code_guard,
        "issues": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form widget precision from contract snapshot.")
    parser.add_argument("--input", default="tmp/json/form.json", help="contract json file path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    result = run_audit(Path(args.input))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result.get("summary") or {}
        print(
            "status={status} blocking={blocking} issues={issues}".format(
                status=summary.get("status"),
                blocking=summary.get("blocking_count"),
                issues=summary.get("issue_count"),
            )
        )
    if args.strict and (result.get("summary") or {}).get("blocking_count", 0) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

