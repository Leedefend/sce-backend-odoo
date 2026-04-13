#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "contract" / "form_render_profile_closure_v1.json"


def _load_payload(input_path: str) -> dict[str, Any]:
    raw = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if isinstance(raw.get("data"), dict):
        return raw.get("data")
    result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
    if isinstance(result.get("data"), dict):
        return result.get("data")
    return raw if isinstance(raw, dict) else {}


def _action_count(surface: dict[str, Any], key: str) -> int:
    actions = (surface.get("actions") if isinstance(surface.get("actions"), dict) else {}).get(key)
    return len(actions) if isinstance(actions, list) else 0


def run_audit(input_path: str) -> dict[str, Any]:
    data = _load_payload(input_path)
    render_surfaces = data.get("render_surfaces") if isinstance(data.get("render_surfaces"), dict) else {}

    issues: list[str] = []
    for key in ("create", "edit", "readonly"):
        if not isinstance(render_surfaces.get(key), dict):
            issues.append(f"MISSING_SURFACE_{key.upper()}")

    create = render_surfaces.get("create") if isinstance(render_surfaces.get("create"), dict) else {}
    edit = render_surfaces.get("edit") if isinstance(render_surfaces.get("edit"), dict) else {}
    readonly = render_surfaces.get("readonly") if isinstance(render_surfaces.get("readonly"), dict) else {}

    create_header = _action_count(create, "header_buttons")
    edit_header = _action_count(edit, "header_buttons")
    readonly_header = _action_count(readonly, "header_buttons")

    create_stat = _action_count(create, "stat_buttons")
    edit_stat = _action_count(edit, "stat_buttons")
    readonly_stat = _action_count(readonly, "stat_buttons")

    if not (edit_header >= create_header >= readonly_header):
        issues.append("HEADER_ACTION_DIFF_NOT_VALID")
    if create_stat != 0:
        issues.append("CREATE_STAT_BUTTONS_SHOULD_BE_EMPTY")
    if edit_stat < readonly_stat:
        issues.append("EDIT_STAT_BUTTONS_SHOULD_COVER_READONLY")

    readonly_flag = bool(readonly.get("readonly", False))
    if not readonly_flag:
        issues.append("READONLY_SURFACE_FLAG_MISSING")

    payload = {
        "version": "v1",
        "audit": "form_render_profile_closure",
        "target": {"input": input_path},
        "summary": {
            "status": "PASS" if not issues else "BLOCKED",
            "issue_count": len(issues),
        },
        "metrics": {
            "create_header": create_header,
            "edit_header": edit_header,
            "readonly_header": readonly_header,
            "create_stat": create_stat,
            "edit_stat": edit_stat,
            "readonly_stat": readonly_stat,
            "readonly_flag": readonly_flag,
            "create_fields": len(create.get("field_names") or []),
            "edit_fields": len(edit.get("field_names") or []),
            "readonly_fields": len(readonly.get("field_names") or []),
        },
        "issues": issues,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit form render profile closure.")
    parser.add_argument("--input", default="tmp/json/form.json")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    payload = run_audit(args.input)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "status={status} issue_count={issue_count}".format(
                status=payload["summary"]["status"],
                issue_count=payload["summary"]["issue_count"],
            )
        )
    if args.strict and payload["summary"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
