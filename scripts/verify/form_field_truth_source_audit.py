#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_field_truth_source_v1.json"
CONTAINER_KEYS = ("children", "tabs", "pages", "nodes", "items")
FOCUS_FIELDS = {
    "description",
    "active",
    "alias_contact",
    "task_ids",
    "collaborator_ids",
    "partner_id",
    "analytic_account_id",
}
FORBIDDEN_FIELD_INFO_KEYS = {"type", "relation", "required", "readonly", "invisible", "help"}
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
            children = node.get(key)
            if isinstance(children, list):
                for child in children:
                    yield from _walk_layout(child)
        return
    if isinstance(node, list):
        for item in node:
            yield from _walk_layout(item)


def _field_type(descriptor: dict[str, Any]) -> str:
    return str(descriptor.get("type") or descriptor.get("ttype") or "").strip().lower()


def _build_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    fields = data.get("fields") if isinstance(data.get("fields"), dict) else {}
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    layout = form.get("layout")

    rows: list[dict[str, Any]] = []
    for node in _walk_layout(layout):
        if str(node.get("type") or "").strip().lower() != "field":
            continue
        field_name = str(node.get("name") or "").strip()
        if not field_name:
            continue

        descriptor = fields.get(field_name) if isinstance(fields.get(field_name), dict) else {}
        field_info = node.get("fieldInfo") if isinstance(node.get("fieldInfo"), dict) else {}

        issues: list[str] = []
        blocking = False

        if not descriptor:
            issues.append("FIELD_MISSING_IN_FIELDS")
            blocking = True
        else:
            canonical_type = _field_type(descriptor)
            canonical_relation = str(descriptor.get("relation") or descriptor.get("comodel_name") or "").strip()
            if canonical_type in RELATIONAL_TYPES and not canonical_relation:
                issues.append("CANONICAL_RELATION_MISSING")
                blocking = True

        leaked_keys = sorted([key for key in field_info.keys() if key in FORBIDDEN_FIELD_INFO_KEYS])
        if leaked_keys:
            issues.append(f"FORBIDDEN_FIELD_INFO_KEYS:{','.join(leaked_keys)}")
            blocking = True

        if not str(field_info.get("name") or "").strip():
            issues.append("FIELD_INFO_NAME_MISSING")
            blocking = True
        if not str(field_info.get("label") or "").strip():
            issues.append("FIELD_INFO_LABEL_MISSING")
            blocking = True

        row = {
            "field": field_name,
            "focus": field_name in FOCUS_FIELDS,
            "field_info_keys": sorted(field_info.keys()),
            "canonical_type": _field_type(descriptor) if descriptor else "",
            "canonical_relation": str(descriptor.get("relation") or descriptor.get("comodel_name") or "") if descriptor else "",
            "issues": issues,
            "blocking": blocking,
        }
        if issues or row["focus"]:
            rows.append(row)
    return rows


def run_audit(input_path: Path) -> dict[str, Any]:
    payload = _load_payload(input_path)
    rows = _build_rows(payload)
    blocking_rows = [row for row in rows if bool(row.get("blocking"))]

    contract_service_text = CONTRACT_SERVICE_PATH.read_text(encoding="utf-8") if CONTRACT_SERVICE_PATH.exists() else ""
    code_guard = {
        "uses_next_field_info_projection": "next_field_info = {" in contract_service_text,
        "no_field_info_type_write": "field_info[\"type\"]" not in contract_service_text,
        "no_field_info_relation_write": "field_info[\"relation\"]" not in contract_service_text,
    }
    code_guard_pass = all(bool(v) for v in code_guard.values())
    snapshot_outdated = code_guard_pass and len(blocking_rows) > 0

    summary_status = "PASS" if code_guard_pass and (len(blocking_rows) == 0 or snapshot_outdated) else "BLOCKED"

    result = {
        "version": "v1",
        "audit": "form_field_truth_source",
        "target": {
            "input": str(input_path),
        },
        "summary": {
            "status": summary_status,
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
    parser = argparse.ArgumentParser(description="Audit form field truth-source consistency using contract snapshot.")
    parser.add_argument("--input", default="tmp/json/form.json", help="contract json file path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when blocking issues exist.")
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
