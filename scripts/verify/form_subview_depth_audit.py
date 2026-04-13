#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_subview_depth_v1.json"


def _load_payload(input_path: str) -> dict[str, Any]:
    raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if isinstance(raw.get("data"), dict):
        return raw.get("data")
    result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
    if isinstance(result.get("data"), dict):
        return result.get("data")
    return raw if isinstance(raw, dict) else {}


def run_audit(input_path: str) -> dict[str, Any]:
    data = _load_payload(input_path)
    form = ((data.get("views") or {}).get("form") or {}) if isinstance(data, dict) else {}
    subviews = form.get("subviews") if isinstance(form.get("subviews"), dict) else {}
    fields_meta = data.get("fields") if isinstance(data.get("fields"), dict) else {}

    issues: list[str] = []
    details: list[dict[str, Any]] = []

    for field_name, node in subviews.items():
        if not isinstance(node, dict):
            continue
        fmeta = fields_meta.get(field_name) if isinstance(fields_meta.get(field_name), dict) else {}
        ftype = str(fmeta.get("type") or fmeta.get("ttype") or "").strip().lower()
        if ftype not in {"one2many", "many2many"}:
            continue

        tree = node.get("tree") if isinstance(node.get("tree"), dict) else {}
        columns = tree.get("columns") if isinstance(tree.get("columns"), list) else []
        sub_fields = node.get("fields") if isinstance(node.get("fields"), dict) else {}
        relation_model = str(node.get("relation_model") or "").strip()
        policies = node.get("policies") if isinstance(node.get("policies"), dict) else {}

        missing_column_meta = [col for col in columns if col not in sub_fields]
        if not columns:
            issues.append(f"{field_name}:TREE_COLUMNS_EMPTY")
        if not sub_fields:
            issues.append(f"{field_name}:SUBVIEW_FIELDS_EMPTY")
        if missing_column_meta:
            issues.append(f"{field_name}:COLUMN_META_MISSING")
        if not relation_model:
            issues.append(f"{field_name}:RELATION_MODEL_MISSING")
        if "inline_edit" not in policies:
            issues.append(f"{field_name}:POLICY_INLINE_EDIT_MISSING")

        details.append(
            {
                "field": field_name,
                "type": ftype,
                "columns": len(columns),
                "fields": len(sub_fields),
                "relation_model": relation_model,
                "missing_column_meta": missing_column_meta,
            }
        )

    payload = {
        "version": "v1",
        "audit": "form_subview_depth",
        "target": {"input": input_path},
        "summary": {
            "status": "PASS" if not issues else "BLOCKED",
            "issue_count": len(issues),
            "x2many_subview_count": len(details),
        },
        "details": details,
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit x2many form subview depth.")
    parser.add_argument("--input", default="tmp/json/form.json")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args.input)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "status={status} subviews={count}".format(
                status=payload["summary"]["status"],
                count=payload["summary"]["x2many_subview_count"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
