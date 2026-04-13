#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_layout_single_source_v1.json"
CONTAINER_KEYS = ("children", "tabs", "pages", "nodes", "items")
CONTRACT_SERVICE_PATH = ROOT / "addons" / "smart_core" / "app_config_engine" / "services" / "contract_service.py"
LOAD_CONTRACT_PATH = ROOT / "addons" / "smart_core" / "handlers" / "load_contract.py"


def _load_payload(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    loaded = json.loads(text)
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


def _has_field_nodes(layout: Any) -> bool:
    for node in _walk_layout(layout):
        if str(node.get("type") or "").strip().lower() == "field":
            return True
    return False


def run_audit(input_path: Path) -> dict[str, Any]:
    payload = _load_payload(input_path)
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form_view = views.get("form") if isinstance(views.get("form"), dict) else {}
    view_layout = form_view.get("layout")

    semantic_page = data.get("semantic_page") if isinstance(data.get("semantic_page"), dict) else {}
    form_semantics = semantic_page.get("form_semantics") if isinstance(semantic_page.get("form_semantics"), dict) else {}
    semantic_layout = form_semantics.get("layout")
    layout_source = str(form_semantics.get("layout_source") or "").strip()

    has_view_layout = isinstance(view_layout, list) and len(view_layout) > 0
    has_semantic_layout_tree = isinstance(semantic_layout, (list, dict)) and _has_field_nodes(semantic_layout)
    has_view_layout_fields = _has_field_nodes(view_layout)

    issues: list[str] = []
    if not has_view_layout:
        issues.append("views.form.layout missing or empty")
    if has_semantic_layout_tree:
        issues.append("semantic_page.form_semantics.layout still contains full layout tree")
    if has_view_layout and not has_view_layout_fields:
        issues.append("views.form.layout has no field nodes")
    if layout_source != "views.form.layout":
        issues.append("form_semantics.layout_source is not views.form.layout")

    contract_service_text = CONTRACT_SERVICE_PATH.read_text(encoding="utf-8") if CONTRACT_SERVICE_PATH.exists() else ""
    load_contract_text = LOAD_CONTRACT_PATH.read_text(encoding="utf-8") if LOAD_CONTRACT_PATH.exists() else ""
    code_guard = {
        "contract_service_removes_semantic_layout": "form_semantics.pop(\"layout\", None)" in contract_service_text,
        "contract_service_sets_layout_source": "form_semantics[\"layout_source\"] = \"views.form.layout\"" in contract_service_text,
        "load_contract_sets_layout_source": "\"layout_source\": \"views.form.layout\"" in load_contract_text,
        "load_contract_no_layout_duplication": "\"layout\": layout," not in load_contract_text,
    }
    code_guard_pass = all(bool(v) for v in code_guard.values())

    snapshot_outdated = (
        code_guard_pass
        and has_semantic_layout_tree
        and layout_source != "views.form.layout"
    )
    status = "PASS" if (not issues or snapshot_outdated) and code_guard_pass else "BLOCKED"

    result = {
        "version": "v1",
        "audit": "form_layout_single_source",
        "target": {
            "input": str(input_path),
        },
        "summary": {
            "status": status,
            "issue_count": len(issues),
            "has_view_layout": has_view_layout,
            "has_view_layout_fields": has_view_layout_fields,
            "has_semantic_layout_tree": has_semantic_layout_tree,
            "layout_source": layout_source,
            "snapshot_outdated": snapshot_outdated,
            "code_guard_pass": code_guard_pass,
        },
        "code_guard": code_guard,
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit single truth-source for form layout.")
    parser.add_argument("--input", default="tmp/json/form.json", help="contract json file path")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    input_path = Path(args.input)
    result = run_audit(input_path)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        summary = result.get("summary") or {}
        print(
            "status={status} issue_count={issue_count} semantic_layout_tree={semantic_layout_tree}".format(
                status=summary.get("status"),
                issue_count=summary.get("issue_count"),
                semantic_layout_tree=summary.get("has_semantic_layout_tree"),
            )
        )

    if args.strict and (result.get("summary") or {}).get("status") != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
